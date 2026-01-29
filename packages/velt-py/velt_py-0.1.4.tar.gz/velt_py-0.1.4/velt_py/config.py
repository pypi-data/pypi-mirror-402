"""
Configuration management for Velt SDK
"""
import os
from typing import Dict, Optional, Any
from urllib.parse import quote_plus


class Config:
    """Configuration validator and MongoDB URI builder"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize configuration
        
        Args:
            config: Configuration dictionary with database and optional API settings
        """
        self.config = config
        self._validate_config()
        self._build_mongodb_uri()
    
    def _validate_config(self):
        """Validate required configuration fields"""
        if 'database' not in self.config:
            raise ValueError("Configuration must include 'database' key")
        
        db_config = self.config['database']
        required_fields = ['host', 'username', 'password', 'auth_database', 'database_name']
        
        for field in required_fields:
            if field not in db_config:
                raise ValueError(f"Database configuration must include '{field}'")
    
    def _build_mongodb_uri(self):
        """Build MongoDB connection URI from configuration"""
        db_config = self.config['database']
        
        # Support connection string override
        if 'connection_string' in db_config and db_config['connection_string']:
            # Use connection string as-is - SRV connections handle TLS automatically
            self.mongodb_uri = db_config['connection_string']
            return
        
        # Build URI from components
        username = quote_plus(db_config['username'])
        password = quote_plus(db_config['password'])
        host = db_config['host']
        database_name = db_config['database_name']
        auth_database = db_config['auth_database']
        
        # Check if SRV connection is needed (MongoDB Atlas uses .mongodb.net domains)
        # For Atlas, always prefer mongodb+srv:// as it handles TLS automatically
        is_atlas = '.mongodb.net' in host
        use_srv = db_config.get('use_srv', False) or is_atlas
        
        # Handle different host formats
        if host.startswith('mongodb://') or host.startswith('mongodb+srv://'):
            # Already a connection string
            if 'mongodb+srv://' in host:
                # SRV connection string - use as-is (already has TLS)
                self.mongodb_uri = f"mongodb+srv://{username}:{password}@{host.replace('mongodb+srv://', '').split('/')[0]}/{database_name}?authSource={auth_database}"
            else:
                # Standard connection string - if Atlas, convert to SRV or add TLS
                if is_atlas:
                    # Convert to SRV for better TLS handling
                    host_clean = host.replace('mongodb://', '').split('/')[0]
                    self.mongodb_uri = f"mongodb+srv://{username}:{password}@{host_clean}/{database_name}?authSource={auth_database}&retryWrites=true&w=majority"
                else:
                    self.mongodb_uri = f"mongodb://{username}:{password}@{host.replace('mongodb://', '').split('/')[0]}/{database_name}?authSource={auth_database}"
        else:
            # Simple host format
            if use_srv or is_atlas:
                # MongoDB Atlas SRV connection (recommended for Atlas)
                self.mongodb_uri = f"mongodb+srv://{username}:{password}@{host}/{database_name}?authSource={auth_database}&retryWrites=true&w=majority"
            else:
                # Standard MongoDB connection
                self.mongodb_uri = f"mongodb://{username}:{password}@{host}/{database_name}?authSource={auth_database}"
    
    def get_mongodb_uri(self) -> str:
        """Get MongoDB connection URI"""
        return self.mongodb_uri
    
    def get_database_name(self) -> str:
        """Get database name"""
        return self.config['database']['database_name']
    
    def get_database_type(self) -> str:
        """
        Get database type from config
        
        Returns:
            Database type ('mongodb', 'postgresql', etc.). Defaults to 'mongodb'.
        """
        return self.config.get('database', {}).get('type', 'mongodb')
    
    def get_api_key(self) -> Optional[str]:
        """Get Velt API key from config or environment"""
        if 'apiKey' in self.config:
            return self.config['apiKey']
        return os.getenv('VELT_API_KEY')
    
    def get_auth_token(self) -> Optional[str]:
        """Get Velt auth token from config or environment"""
        if 'authToken' in self.config:
            return self.config['authToken']
        return os.getenv('VELT_AUTH_TOKEN')
    
    def get_user_schema(self) -> Optional[Dict[str, Any]]:
        """
        Get user schema mapping from config
        
        Returns:
            Dictionary mapping SDK field names to customer field names.
            Values can be:
            - A string: Direct field name mapping (supports dot notation for nested fields)
            - A list: Try these field names in order until one is found (supports nested fields)
            
        Note:
            Standard SDK fields (userId, name, email, photoUrl, color, textColor, isAdmin, initial)
            are always included in the response, even if not specified in the schema. If not mapped,
            they will use the SDK field name directly.
            
            Custom fields are only included if explicitly specified in this schema. This ensures
            explicit control over which custom fields are exposed.
            
        Example:
            {
                # Standard SDK fields (optional - will use SDK field name if not specified)
                'userId': ['userId', 'id', 'user_id'],  # Try these in order
                'name': 'full_name',  # Direct mapping
                'email': 'email_address',
                'photoUrl': 'photo_url',
                # Note: 'color', 'textColor', 'isAdmin', 'initial' not specified - will use SDK names
                
                # Custom fields (must be explicitly specified to be included)
                'department': 'dept',        # Map customer's 'dept' field → 'department' in response
                'role': 'user_role',         # Map customer's 'user_role' field → 'role' in response
                'phone': 'phone_number'       # Map customer's 'phone_number' field → 'phone' in response
            }
            # Standard SDK fields always included, custom fields only if listed above
        """
        return self.config.get('user_schema')
    
    def get_collection_name(self, collection_type: str) -> str:
        """
        Get collection name for a given collection type
        
        Args:
            collection_type: Type of collection ('comments', 'reactions', 'attachments', 'users')
            
        Returns:
            Collection name (defaults to standard names if not configured)
            
        Example:
            Config with custom collection names:
            {
                'collections': {
                    'comments': 'my_comments',
                    'reactions': 'my_reactions',
                    'attachments': 'my_attachments',
                    'users': 'my_users'
                }
            }
        """
        collections = self.config.get('collections', {})
        default_names = {
            'comments': 'comment_annotations',
            'reactions': 'reaction_annotations',
            'attachments': 'attachments',
            'users': 'users'
        }
        return collections.get(collection_type, default_names.get(collection_type, collection_type))
    
    def get_aws_config(self) -> Optional[Dict[str, Any]]:
        """
        Get AWS S3 configuration
        
        Returns:
            Dictionary with AWS config:
            {
                'access_key_id': str,
                'secret_access_key': str,
                'region': str,
                'bucket_name': str,
                'endpoint_url': Optional[str]  # For S3-compatible services
            }
            Returns None if AWS config is not provided
        """
        aws_config = self.config.get('aws', {})
        if not aws_config:
            return None
        
        access_key_id = aws_config.get('access_key_id') or os.getenv('AWS_ACCESS_KEY_ID')
        secret_access_key = aws_config.get('secret_access_key') or os.getenv('AWS_SECRET_ACCESS_KEY')
        bucket_name = aws_config.get('bucket_name') or os.getenv('AWS_S3_BUCKET_NAME')
        
        if not bucket_name:
            return None
        
        return {
            'access_key_id': access_key_id,
            'secret_access_key': secret_access_key,
            'region': aws_config.get('region') or os.getenv('AWS_REGION', 'us-east-1'),
            'bucket_name': bucket_name,
            'endpoint_url': aws_config.get('endpoint_url') or os.getenv('AWS_S3_ENDPOINT_URL')
        }
    
    def is_s3_enabled(self) -> bool:
        """
        Check if S3 storage is enabled
        
        Returns:
            True if S3 configuration is available, False otherwise
        """
        aws_config = self.get_aws_config()
        return aws_config is not None and aws_config.get('bucket_name') is not None

