"""
S3 storage service for file uploads
"""
from typing import Optional, Dict, Any
import uuid

from ...exceptions import VeltSDKError


def _get_boto3():
    """Lazy import boto3 to avoid import errors if not installed"""
    try:
        import boto3
        from botocore.exceptions import ClientError
        return boto3, ClientError
    except ImportError:
        raise ImportError(
            "boto3 is required for S3 storage. Install it with: pip install boto3>=1.28.0"
        )


class S3Service:
    """Service for uploading files to AWS S3"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize S3 service
        
        Args:
            config: AWS configuration dictionary
        """
        self.access_key_id = config.get('access_key_id')
        self.secret_access_key = config.get('secret_access_key')
        self.region = config.get('region', 'us-east-1')
        self.bucket_name = config.get('bucket_name')
        self.endpoint_url = config.get('endpoint_url')
        
        if not self.bucket_name:
            raise ValueError("bucket_name is required for S3 storage")
        
        # Initialize S3 client (lazy import)
        boto3, ClientError = _get_boto3()
        self._boto3 = boto3
        self._ClientError = ClientError
        
        s3_kwargs = {
            'aws_access_key_id': self.access_key_id,
            'aws_secret_access_key': self.secret_access_key,
            'region_name': self.region
        }
        
        if self.endpoint_url:
            s3_kwargs['endpoint_url'] = self.endpoint_url
        
        self.s3_client = boto3.client('s3', **s3_kwargs)
    
    def upload_file(
        self,
        file_data: bytes,
        file_name: str,
        mime_type: Optional[str] = None,
        api_key: Optional[str] = None,
        folder_prefix: Optional[str] = None
    ) -> str:
        """
        Upload file to S3
        
        Args:
            file_data: File content as bytes
            file_name: Original file name
            mime_type: MIME type of the file
            api_key: API key for folder structure
            folder_prefix: Optional folder prefix (e.g., 'attachments')
            
        Returns:
            S3 URL of uploaded file
        """
        try:
            # Generate unique file key
            file_extension = file_name.split('.')[-1] if '.' in file_name else ''
            unique_id = str(uuid.uuid4())
            file_key = f"{unique_id}.{file_extension}" if file_extension else unique_id
            
            # Build S3 key with optional folder structure
            s3_key_parts = []
            if folder_prefix:
                s3_key_parts.append(folder_prefix)
            if api_key:
                s3_key_parts.append(api_key)
            s3_key_parts.append(file_key)
            
            s3_key = '/'.join(s3_key_parts)
            
            # Upload to S3
            upload_kwargs = {
                'Bucket': self.bucket_name,
                'Key': s3_key,
                'Body': file_data
            }
            
            if mime_type:
                upload_kwargs['ContentType'] = mime_type
            
            self.s3_client.put_object(**upload_kwargs)
            
            # Return public URL or presigned URL
            if self.endpoint_url:
                # Custom endpoint (e.g., DigitalOcean Spaces, MinIO)
                url = f"{self.endpoint_url}/{self.bucket_name}/{s3_key}"
            else:
                # Standard S3 URL
                url = f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com/{s3_key}"
            
            return url
            
        except self._ClientError as e:
            raise VeltSDKError(f"Failed to upload file to S3: {str(e)}")
        except Exception as e:
            raise VeltSDKError(f"Unexpected error uploading file to S3: {str(e)}")
    
    def delete_file(self, s3_url_or_key: str) -> bool:
        """
        Delete file from S3
        
        Args:
            s3_url_or_key: S3 URL or S3 key of the file to delete
                          - URL format: https://bucket.s3.region.amazonaws.com/key
                          - Key format: attachments/api-key/uuid.txt
            
        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            # If it's already a key (doesn't start with http), use it directly
            if not (s3_url_or_key.startswith('http://') or s3_url_or_key.startswith('https://')):
                s3_key = s3_url_or_key
            else:
                # Extract S3 key from URL
                s3_key = self._extract_key_from_url(s3_url_or_key)
            
            if not s3_key:
                return False
            
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=s3_key)
            return True
            
        except self._ClientError as e:
            # File might not exist, log but don't fail
            print(f"Warning: Failed to delete file from S3: {str(e)}")
            return False
        except Exception as e:
            print(f"Warning: Unexpected error deleting file from S3: {str(e)}")
            return False
    
    def _extract_key_from_url(self, s3_url: str) -> Optional[str]:
        """Extract S3 key from URL"""
        try:
            # Handle different URL formats
            if 'amazonaws.com' in s3_url:
                # Standard S3 URL: https://bucket.s3.region.amazonaws.com/key
                parts = s3_url.split('.amazonaws.com/')
                if len(parts) > 1:
                    return parts[1]
            elif '/' in s3_url:
                # Custom endpoint or simple format
                parts = s3_url.split('/')
                # Find bucket name and extract key after it
                bucket_index = None
                for i, part in enumerate(parts):
                    if part == self.bucket_name:
                        bucket_index = i
                        break
                if bucket_index is not None and bucket_index + 1 < len(parts):
                    return '/'.join(parts[bucket_index + 1:])
            return None
        except Exception:
            return None
