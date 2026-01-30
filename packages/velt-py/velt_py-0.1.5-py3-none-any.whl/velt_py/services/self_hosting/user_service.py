"""
User service for managing users
"""
from typing import Dict, Any, List, Optional, Union
from pymongo.errors import PyMongoError

from .base_service import BaseService
from ...exceptions import VeltValidationError
from ...config import Config
from ...models import ResolverResponse, GetUserResolverRequest, User


class UserService(BaseService):
    """Service for managing users"""
    
    def __init__(self, database, config: Optional[Config] = None):
        """
        Initialize user service
        
        Args:
            database: DatabaseAdapter instance
            config: Optional configuration instance for schema mapping
        """
        super().__init__(database)
        self.collection_name = config.get_collection_name('users') if config else 'users'
        self.config = config
        self._user_schema = None
        self._load_user_schema()
    
    def _load_user_schema(self):
        """Load user schema mapping from config"""
        if self.config:
            self._user_schema = self.config.get_user_schema()
    
    def _get_nested_value(self, doc: Dict[str, Any], path: str) -> Any:
        """
        Get nested value from document using dot notation
        
        Args:
            doc: Document dictionary
            path: Dot-separated path (e.g., 'profile.name', 'metadata.user.email')
            
        Returns:
            Value at path or None if not found
        """
        keys = path.split('.')
        value = doc
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
                if value is None:
                    return None
            else:
                return None
        return value
    
    def _get_field_value(self, doc: Dict[str, Any], sdk_field: str, try_sdk_name_fallback: bool = True) -> Any:
        """
        Get field value from document using schema mapping
        
        Supports both top-level and nested fields using dot notation.
        For standard SDK fields, will try the mapped name first, then fallback to SDK field name.
        
        Args:
            doc: MongoDB document
            sdk_field: SDK field name (e.g., 'userId', 'name')
            try_sdk_name_fallback: If True, try SDK field name as fallback when mapping exists
            
        Returns:
            Field value or None if not found
        """
        if not self._user_schema or sdk_field not in self._user_schema:
            # No schema mapping, use SDK field name directly
            # Check if it's nested first
            if '.' in sdk_field:
                return self._get_nested_value(doc, sdk_field)
            return doc.get(sdk_field)
        
        mapping = self._user_schema[sdk_field]
        
        if isinstance(mapping, str):
            # Direct mapping: 'userId' -> 'id' or 'name' -> 'profile.name'
            if '.' in mapping:
                value = self._get_nested_value(doc, mapping)
                if value is not None:
                    return value
            else:
                value = doc.get(mapping)
                if value is not None:
                    return value
            
            # Fallback to SDK field name if mapping didn't find a value
            # This handles cases where document has SDK field name directly
            if try_sdk_name_fallback:
                if '.' in sdk_field:
                    return self._get_nested_value(doc, sdk_field)
                return doc.get(sdk_field)
            return None
        elif isinstance(mapping, list):
            # Try multiple field names in order
            for field_name in mapping:
                if '.' in field_name:
                    # Nested field path
                    value = self._get_nested_value(doc, field_name)
                    if value is not None:
                        return value
                else:
                    # Top-level field
                    if field_name in doc:
                        return doc.get(field_name)
            
            # Fallback to SDK field name if none of the mapped names found a value
            if try_sdk_name_fallback:
                if '.' in sdk_field:
                    return self._get_nested_value(doc, sdk_field)
                return doc.get(sdk_field)
            return None
        else:
            # Invalid mapping type, fallback to SDK field name
            if '.' in sdk_field:
                return self._get_nested_value(doc, sdk_field)
            return doc.get(sdk_field)
    
    def _transform_user(self, user_doc: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform user document from customer schema to SDK schema
        
        Always includes standard SDK fields (even if not in schema, uses SDK field name).
        Only includes custom fields if they are explicitly specified in user_schema.
        This ensures customers have explicit control over custom fields while standard
        fields always work.
        
        Args:
            user_doc: Raw MongoDB document
            
        Returns:
            Transformed user document with SDK field names. Standard SDK fields are always
            included, custom fields only if specified in user_schema.
        """
        if not self._user_schema:
            # No schema mapping, return as-is (remove _id)
            user_doc.pop('_id', None)
            return user_doc
        
        transformed: Dict[str, Any] = {}
        
        # Standard SDK fields - always try to include these
        # (will use schema mapping if available, otherwise SDK field name)
        standard_sdk_fields = [
            'userId',      # Required: Unique user identifier
            'name',         # Optional: User's full name
            'photoUrl',     # Optional: Display picture URL
            'email',        # Optional: Email for notifications
            'color',        # Optional: Avatar border and cursor color
            'textColor',    # Optional: Avatar text color
            'isAdmin',      # Optional: Admin flag
            'initial',      # Optional: Initial character
            'organizationId'  # Optional: For data isolation (internal use)
        ]
        
        # Always process standard SDK fields
        for sdk_field in standard_sdk_fields:
            value = self._get_field_value(user_doc, sdk_field)
            if value is not None:
                transformed[sdk_field] = value
        
        # Only process custom fields if they are explicitly specified in user_schema
        # This gives customers explicit control over which custom fields are exposed
        for sdk_field, mapping in self._user_schema.items():
            # Skip if it's already a standard SDK field (already processed above)
            if sdk_field not in standard_sdk_fields:
                value = self._get_field_value(user_doc, sdk_field)
                if value is not None:
                    transformed[sdk_field] = value
        
        return transformed
    
    def _get_user_id_field(self) -> Union[str, List[str]]:
        """
        Get the field name(s) to use for userId in queries
        
        Returns:
            Field name string or list of field names to try
        """
        if not self._user_schema or 'userId' not in self._user_schema:
            return 'userId'
        
        mapping = self._user_schema['userId']
        if isinstance(mapping, str):
            return mapping
        elif isinstance(mapping, list):
            return mapping
        else:
            return 'userId'
    
    def getUsers(self, request: GetUserResolverRequest) -> Dict[str, Any]:
        """
        Get users by their IDs
        
        Args:
            request: GetUserResolverRequest object containing organizationId and userIds
            
        Returns:
            Response dictionary with 'success', 'statusCode', and 'data' keys
            Data format: Record<string, User>
        """
        try:
            if not request.userIds or not isinstance(request.userIds, list):
                # Return empty result using ResolverResponse format
                return ResolverResponse(data={}, success=True, statusCode=200).to_dict()
            
            # Build query using schema mapping
            user_id_field = self._get_user_id_field()
            
            # Build query filter
            query_filter: Dict[str, Any] = {}
            
            if isinstance(user_id_field, list):
                # Try to match any of the field names (OR condition)
                # MongoDB doesn't support OR for field names directly, so we'll query each
                # For simplicity, use the first field name and let transformation handle it
                query_filter[user_id_field[0]] = {'$in': request.userIds}
            else:
                query_filter[user_id_field] = {'$in': request.userIds}
            
            # Query database using adapter
            users = self.database.find(self.collection_name, query_filter)
            
            # Transform and convert to Record<string, User> format expected by Velt
            result: Dict[str, Dict[str, Any]] = {}
            for user in users:
                # Transform user document using schema
                transformed_user = self._transform_user(user)
                
                # Get userId from transformed document (should be in SDK format now)
                user_id = transformed_user.get('userId')
                if user_id:
                    # Convert to User model and then to dict
                    user_obj = User.from_dict(transformed_user)
                    result[user_id] = user_obj.to_dict()
            
            # Use ResolverResponse format (like getComments)
            return ResolverResponse(data=result, success=True, statusCode=200).to_dict()
            
        except VeltValidationError as e:
            # Return error dictionary instead of raising
            return {
                'success': False,
                'statusCode': 400,
                'error': str(e),
                'errorCode': 'VALIDATION_ERROR'
            }
        except PyMongoError as e:
            # Return error dictionary instead of raising
            return {
                'success': False,
                'statusCode': 500,
                'error': f"Database error while getting users: {str(e)}",
                'errorCode': 'DATABASE_ERROR'
            }
        except Exception as e:
            # Return error dictionary instead of raising
            return {
                'success': False,
                'statusCode': 500,
                'error': f"Unexpected error while getting users: {str(e)}",
                'errorCode': 'INTERNAL_ERROR'
            }

