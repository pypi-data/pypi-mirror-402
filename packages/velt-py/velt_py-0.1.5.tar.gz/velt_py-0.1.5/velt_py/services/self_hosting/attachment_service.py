"""
Attachment service for managing file attachments
"""
from typing import Dict, Any, Optional
from pymongo.errors import PyMongoError

from .base_service import BaseService
from ...exceptions import VeltDatabaseError, VeltValidationError
from ...models import (
    SaveAttachmentResolverRequest,
    SaveAttachmentResolverData,
    DeleteAttachmentResolverRequest,
    ResolverResponse,
    ResolverAttachment
)
from ...services.storage.s3_service import S3Service


class AttachmentService(BaseService):
    """Service for managing file attachments"""
    
    def __init__(self, database, config=None):
        """
        Initialize attachment service
        
        Args:
            database: DatabaseAdapter instance
            config: Optional Config instance for API key access
        """
        super().__init__(database)
        self.collection_name = config.get_collection_name('attachments') if config else 'attachments'
        self.config = config
    
    def getAttachment(self, organizationId: str, attachmentId: int) -> Dict[str, Any]:
        """
        Get an attachment by ID
        
        Args:
            organizationId: Organization ID (required for data isolation)
            attachmentId: Attachment ID to retrieve
            
        Returns:
            Response dictionary with 'success' and 'data' keys
        """
        try:
            self._validate_organization_id(organizationId)
            
            if attachmentId is None:
                return self._error_response("attachmentId is required", "INVALID_INPUT")
            
            # Query with organizationId filter for data isolation
            # According to BaseMetadata, organizationId is stored in metadata
            attachment = self.database.find_one(
                self.collection_name,
                {
                    'attachmentId': attachmentId,
                    'metadata.organizationId': organizationId
                }
            )
            
            if not attachment:
                return self._error_response(
                    "Attachment not found or does not belong to organization",
                    "NOT_FOUND"
                )
            
            # Remove MongoDB _id field for cleaner response
            attachment.pop('_id', None)
            
            return self._success_response(data=attachment)
            
        except VeltValidationError:
            raise
        except PyMongoError as e:
            raise VeltDatabaseError(f"Database error while getting attachment: {str(e)}")
        except Exception as e:
            raise VeltDatabaseError(f"Unexpected error while getting attachment: {str(e)}")
    
    def saveAttachment(
        self,
        request: SaveAttachmentResolverRequest,
        file_data: Optional[bytes] = None,
        file_name: Optional[str] = None,
        mime_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Save an attachment based on SaveAttachmentResolverRequest
        
        If file_data is provided, uploads to S3 first and sets the URL in the request.
        Otherwise, expects attachment.file to already be an S3 URL.
        
        Args:
            request: SaveAttachmentResolverRequest object containing attachment and metadata
            file_data: Optional file bytes to upload to S3
            file_name: Optional file name (used if file_data provided)
            mime_type: Optional MIME type (used if file_data provided)
            
        Returns:
            ResolverResponse format: { 'data': SaveAttachmentResolverData, 'success': bool, 'statusCode': int }
        """
        try:
            # Get organizationId from metadata
            organization_id = None
            if request.metadata:
                organization_id = request.metadata.organizationId
            
            if not organization_id:
                return {
                    'success': False,
                    'statusCode': 400,
                    'error': 'organizationId is required in metadata',
                    'errorCode': 'INVALID_INPUT'
                }
            
            self._validate_organization_id(organization_id)
            
            if not request.attachment:
                return {
                    'success': False,
                    'statusCode': 400,
                    'error': 'attachment is required',
                    'errorCode': 'INVALID_INPUT'
                }
            
            attachment_id = request.attachment.attachmentId
            if attachment_id is None:
                return {
                    'success': False,
                    'statusCode': 400,
                    'error': 'attachment.attachmentId is required',
                    'errorCode': 'INVALID_INPUT'
                }
            
            # Get API key from config if available
            api_key = None
            if self.config:
                api_key = self.config.get_api_key()
            
            # Extract metadata from request
            request_metadata = request.metadata
            document_id = request_metadata.documentId if request_metadata else None
            folder_id = request_metadata.folderId if request_metadata else None
            
            # Handle file upload if file_data is provided
            file_url = None
            if file_data is not None:
                # Validate S3 is enabled
                if not self.config or not self.config.is_s3_enabled():
                    return {
                        'success': False,
                        'statusCode': 500,
                        'error': 'S3 configuration is required for file uploads',
                        'errorCode': 'CONFIGURATION_ERROR'
                    }
                
                # Upload to S3
                try:
                    aws_config = self.config.get_aws_config()
                    if not aws_config:
                        return {
                            'success': False,
                            'statusCode': 500,
                            'error': 'AWS configuration is missing',
                            'errorCode': 'CONFIGURATION_ERROR'
                        }
                    
                    s3_service = S3Service(aws_config)
                    
                    # Get file name and mime type from parameters or request
                    name = file_name
                    if not name:
                        if isinstance(request.attachment, ResolverAttachment):
                            name = request.attachment.name
                        elif isinstance(request.attachment, dict):
                            name = request.attachment.get('name')
                        if not name:
                            name = 'attachment'
                    
                    mime = mime_type
                    if not mime:
                        if isinstance(request.attachment, ResolverAttachment):
                            mime = request.attachment.mimeType
                        elif isinstance(request.attachment, dict):
                            mime = request.attachment.get('mimeType')
                    
                    # Upload to S3
                    file_url = s3_service.upload_file(
                        file_data=file_data,
                        file_name=name,
                        mime_type=mime,
                        api_key=api_key,
                        folder_prefix='attachments'
                    )
                    
                    # Set S3 URL in request attachment
                    if isinstance(request.attachment, ResolverAttachment):
                        request.attachment.file = file_url
                        # Also update name and mimeType if provided
                        if file_name:
                            request.attachment.name = file_name
                        if mime_type:
                            request.attachment.mimeType = mime_type
                    elif isinstance(request.attachment, dict):
                        request.attachment['file'] = file_url
                        if file_name:
                            request.attachment['name'] = file_name
                        if mime_type:
                            request.attachment['mimeType'] = mime_type
                    
                except Exception as e:
                    return {
                        'success': False,
                        'statusCode': 500,
                        'error': f'Failed to upload file to S3: {str(e)}',
                        'errorCode': 'S3_UPLOAD_ERROR'
                    }
            else:
                # Get file URL from attachment (should already be S3 URL)
                if isinstance(request.attachment, ResolverAttachment):
                    file_url = request.attachment.file
                elif isinstance(request.attachment, dict):
                    file_url = request.attachment.get('file')
                
                # Validate that file is a URL (S3 URL)
                if not file_url or not isinstance(file_url, str):
                    return {
                        'success': False,
                        'statusCode': 400,
                        'error': 'attachment.file must be a URL string (S3 URL) or file_data must be provided',
                        'errorCode': 'INVALID_INPUT'
                    }
                
                # Validate URL format
                if not (file_url.startswith('http://') or file_url.startswith('https://')):
                    return {
                        'success': False,
                        'statusCode': 400,
                        'error': 'attachment.file must be a valid URL (http:// or https://)',
                        'errorCode': 'INVALID_INPUT'
                    }
            
            # Convert ResolverAttachment to dict for saving
            if isinstance(request.attachment, ResolverAttachment):
                attachment_data = request.attachment.to_dict()
            else:
                attachment_data = request.attachment.copy() if isinstance(request.attachment, dict) else {}
            
            # Initialize metadata if not present
            if 'metadata' not in attachment_data:
                attachment_data['metadata'] = {}
            
            # Set organizationId in metadata (from request metadata)
            attachment_data['metadata']['organizationId'] = organization_id
            
            # Set documentId in metadata (from request metadata or attachment metadata)
            if document_id:
                attachment_data['metadata']['documentId'] = document_id
            elif attachment_data.get('metadata', {}).get('documentId'):
                # Keep existing documentId from attachment
                pass
            
            # Set folderId in metadata if provided
            if folder_id:
                attachment_data['metadata']['folderId'] = folder_id
            elif attachment_data.get('metadata', {}).get('folderId'):
                # Keep existing folderId from attachment
                pass
            
            # Set apiKey in metadata if available from config
            if api_key:
                attachment_data['metadata']['apiKey'] = api_key
            elif request_metadata and request_metadata.apiKey:
                attachment_data['metadata']['apiKey'] = request_metadata.apiKey
            
            # Store attachment data with S3 URL (not file data)
            self.database.update_one(
                self.collection_name,
                {'attachmentId': attachment_id, 'metadata.organizationId': organization_id},
                {'$set': attachment_data},
                upsert=True
            )
            
            # Return S3 URL in response
            save_data = SaveAttachmentResolverData(url=file_url)
            return ResolverResponse(data=save_data.to_dict(), success=True, statusCode=200).to_dict()
            
        except VeltValidationError:
            raise
        except PyMongoError as e:
            raise VeltDatabaseError(f"Database error while saving attachment: {str(e)}")
        except Exception as e:
            raise VeltDatabaseError(f"Unexpected error while saving attachment: {str(e)}")
    
    def deleteAttachment(self, request: DeleteAttachmentResolverRequest) -> Dict[str, Any]:
        """
        Delete an attachment based on DeleteAttachmentResolverRequest
        
        Args:
            request: DeleteAttachmentResolverRequest object containing attachmentId and metadata
            
        Returns:
            ResolverResponse format: { 'success': bool, 'statusCode': int } (no data field, undefined type)
        """
        try:
            if not request.attachmentId or request.attachmentId == 0:
                return {
                    'success': False,
                    'statusCode': 400,
                    'error': 'attachmentId is required',
                    'errorCode': 'INVALID_INPUT'
                }
            
            # Get attachment first to find S3 URL
            # Always lookup by attachmentId only (attachmentId should be unique)
            attachment = self.database.find_one(
                self.collection_name,
                {'attachmentId': request.attachmentId}
            )
            
            # Delete from S3 if file value exists and S3 is enabled
            # delete_file() handles both URLs and S3 keys
            if attachment and self.config and self.config.is_s3_enabled():
                file_value = attachment.get('file') or attachment.get('url')
                if file_value and isinstance(file_value, str):
                    try:
                        aws_config = self.config.get_aws_config()
                        if aws_config:
                            s3_service = S3Service(aws_config)
                            s3_service.delete_file(file_value)  # Handles both URL and key
                    except Exception as e:
                        # Log error but continue with MongoDB deletion
                        print(f"Warning: Failed to delete file from S3: {str(e)}")
            
            # Delete by attachmentId
            query_filter: Dict[str, Any] = {
                'attachmentId': request.attachmentId
            }
            
            # Delete the attachment using adapter
            result = self.database.delete_one(self.collection_name, query_filter)
            
            # Check if document was deleted (adapter-specific check)
            deleted_count = getattr(result, 'deleted_count', 1 if result else 0)
            if deleted_count == 0:
                return {
                    'success': False,
                    'statusCode': 404,
                    'error': 'Attachment not found',
                    'errorCode': 'NOT_FOUND'
                }
            
            # Return ResolverResponse format without data field (just success and statusCode)
            # Return type is Promise<ResolverResponse<undefined>>, so no data field
            return {
                'success': True,
                'statusCode': 200
            }
            
        except PyMongoError as e:
            return {
                'success': False,
                'statusCode': 500,
                'error': f"Database error while deleting attachment: {str(e)}",
                'errorCode': 'DATABASE_ERROR'
            }
        except Exception as e:
            return {
                'success': False,
                'statusCode': 500,
                'error': f"Unexpected error while deleting attachment: {str(e)}",
                'errorCode': 'INTERNAL_ERROR'
            }

