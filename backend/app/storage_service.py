"""
Storage service for handling report storage across different backends (local, S3, Azure Blob)
Supports fallback to local storage when cloud storage fails
"""

import os
import logging
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta
from pathlib import Path

logger = logging.getLogger(__name__)

class StorageService:
    """
    Unified storage service supporting multiple backends with fallback
    """

    def __init__(self, customer):
        """
        Initialize storage service with customer configuration

        Args:
            customer: Customer model instance with storage configuration
        """
        self.customer = customer
        self.storage_type = customer.storage_type if customer else "LOCAL"
        self.fallback_enabled = customer.storage_fallback_enabled if customer else True

    def save_file(self, file_path: str, content: str, content_type: str = "text/plain") -> Tuple[bool, Optional[str]]:
        """
        Save file to configured storage with fallback

        Args:
            file_path: Relative path for the file
            content: Content to save
            content_type: MIME type of content

        Returns:
            Tuple of (success: bool, error_message: Optional[str])
        """
        # Try primary storage
        if self.storage_type == "S3":
            success, error = self._save_to_s3(file_path, content, content_type)
            if success:
                return True, None
            logger.warning(f"S3 storage failed: {error}")

            # Fall back to local if enabled
            if self.fallback_enabled:
                logger.info("Falling back to local storage")
                return self._save_to_local(file_path, content)
            return False, error

        elif self.storage_type == "AZURE_BLOB":
            success, error = self._save_to_azure(file_path, content, content_type)
            if success:
                return True, None
            logger.warning(f"Azure Blob storage failed: {error}")

            # Fall back to local if enabled
            if self.fallback_enabled:
                logger.info("Falling back to local storage")
                return self._save_to_local(file_path, content)
            return False, error

        else:  # LOCAL
            return self._save_to_local(file_path, content)

    def _save_to_local(self, file_path: str, content: str) -> Tuple[bool, Optional[str]]:
        """Save file to local storage"""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            # Write file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)

            logger.info(f"Saved file to local storage: {file_path}")
            return True, None

        except Exception as e:
            error_msg = f"Failed to save to local storage: {str(e)}"
            logger.error(error_msg)
            return False, error_msg

    def _save_to_s3(self, file_path: str, content: str, content_type: str) -> Tuple[bool, Optional[str]]:
        """Save file to S3"""
        try:
            import boto3
            from botocore.exceptions import ClientError, NoCredentialsError

            # Validate configuration
            if not all([self.customer.s3_bucket_name, self.customer.s3_region]):
                return False, "S3 configuration incomplete (missing bucket or region)"

            # Create S3 client
            s3_client = boto3.client(
                's3',
                region_name=self.customer.s3_region,
                aws_access_key_id=self.customer.s3_access_key_id,
                aws_secret_access_key=self.customer.s3_secret_access_key
            )

            # Construct S3 key with optional prefix
            s3_key = file_path
            if self.customer.s3_prefix:
                s3_key = f"{self.customer.s3_prefix.rstrip('/')}/{file_path}"

            # Upload to S3
            s3_client.put_object(
                Bucket=self.customer.s3_bucket_name,
                Key=s3_key,
                Body=content.encode('utf-8'),
                ContentType=content_type
            )

            logger.info(f"Saved file to S3: s3://{self.customer.s3_bucket_name}/{s3_key}")
            return True, None

        except (ClientError, NoCredentialsError) as e:
            error_msg = f"S3 error: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
        except ImportError:
            error_msg = "boto3 library not installed (required for S3 support)"
            logger.error(error_msg)
            return False, error_msg
        except Exception as e:
            error_msg = f"Unexpected S3 error: {str(e)}"
            logger.error(error_msg)
            return False, error_msg

    def _save_to_azure(self, file_path: str, content: str, content_type: str) -> Tuple[bool, Optional[str]]:
        """Save file to Azure Blob Storage"""
        try:
            from azure.storage.blob import BlobServiceClient
            from azure.core.exceptions import AzureError

            # Validate configuration
            if not all([self.customer.azure_connection_string, self.customer.azure_container_name]):
                return False, "Azure Blob configuration incomplete (missing connection string or container)"

            # Create blob service client
            blob_service_client = BlobServiceClient.from_connection_string(
                self.customer.azure_connection_string
            )

            # Construct blob name with optional prefix
            blob_name = file_path
            if self.customer.azure_prefix:
                blob_name = f"{self.customer.azure_prefix.rstrip('/')}/{file_path}"

            # Get blob client
            blob_client = blob_service_client.get_blob_client(
                container=self.customer.azure_container_name,
                blob=blob_name
            )

            # Upload to Azure Blob
            blob_client.upload_blob(
                content.encode('utf-8'),
                content_type=content_type,
                overwrite=True
            )

            logger.info(f"Saved file to Azure Blob: {self.customer.azure_container_name}/{blob_name}")
            return True, None

        except AzureError as e:
            error_msg = f"Azure Blob error: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
        except ImportError:
            error_msg = "azure-storage-blob library not installed (required for Azure Blob support)"
            logger.error(error_msg)
            return False, error_msg
        except Exception as e:
            error_msg = f"Unexpected Azure Blob error: {str(e)}"
            logger.error(error_msg)
            return False, error_msg

    def get_file(self, file_path: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Get file from configured storage with fallback

        Args:
            file_path: Relative path for the file

        Returns:
            Tuple of (content: Optional[str], error_message: Optional[str])
        """
        # Try primary storage
        if self.storage_type == "S3":
            content, error = self._get_from_s3(file_path)
            if content is not None:
                return content, None
            logger.warning(f"S3 retrieval failed: {error}")

            # Fall back to local if enabled
            if self.fallback_enabled:
                logger.info("Falling back to local storage")
                return self._get_from_local(file_path)
            return None, error

        elif self.storage_type == "AZURE_BLOB":
            content, error = self._get_from_azure(file_path)
            if content is not None:
                return content, None
            logger.warning(f"Azure Blob retrieval failed: {error}")

            # Fall back to local if enabled
            if self.fallback_enabled:
                logger.info("Falling back to local storage")
                return self._get_from_local(file_path)
            return None, error

        else:  # LOCAL
            return self._get_from_local(file_path)

    def _get_from_local(self, file_path: str) -> Tuple[Optional[str], Optional[str]]:
        """Get file from local storage"""
        try:
            if not os.path.exists(file_path):
                return None, f"File not found: {file_path}"

            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            return content, None

        except Exception as e:
            error_msg = f"Failed to read from local storage: {str(e)}"
            logger.error(error_msg)
            return None, error_msg

    def _get_from_s3(self, file_path: str) -> Tuple[Optional[str], Optional[str]]:
        """Get file from S3"""
        try:
            import boto3
            from botocore.exceptions import ClientError, NoCredentialsError

            # Validate configuration
            if not all([self.customer.s3_bucket_name, self.customer.s3_region]):
                return None, "S3 configuration incomplete"

            # Create S3 client
            s3_client = boto3.client(
                's3',
                region_name=self.customer.s3_region,
                aws_access_key_id=self.customer.s3_access_key_id,
                aws_secret_access_key=self.customer.s3_secret_access_key
            )

            # Construct S3 key
            s3_key = file_path
            if self.customer.s3_prefix:
                s3_key = f"{self.customer.s3_prefix.rstrip('/')}/{file_path}"

            # Get from S3
            response = s3_client.get_object(
                Bucket=self.customer.s3_bucket_name,
                Key=s3_key
            )

            content = response['Body'].read().decode('utf-8')
            return content, None

        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                return None, "File not found in S3"
            return None, f"S3 error: {str(e)}"
        except Exception as e:
            return None, f"Unexpected S3 error: {str(e)}"

    def _get_from_azure(self, file_path: str) -> Tuple[Optional[str], Optional[str]]:
        """Get file from Azure Blob Storage"""
        try:
            from azure.storage.blob import BlobServiceClient
            from azure.core.exceptions import ResourceNotFoundError, AzureError

            # Validate configuration
            if not all([self.customer.azure_connection_string, self.customer.azure_container_name]):
                return None, "Azure Blob configuration incomplete"

            # Create blob service client
            blob_service_client = BlobServiceClient.from_connection_string(
                self.customer.azure_connection_string
            )

            # Construct blob name
            blob_name = file_path
            if self.customer.azure_prefix:
                blob_name = f"{self.customer.azure_prefix.rstrip('/')}/{file_path}"

            # Get blob client
            blob_client = blob_service_client.get_blob_client(
                container=self.customer.azure_container_name,
                blob=blob_name
            )

            # Download from Azure Blob
            content = blob_client.download_blob().readall().decode('utf-8')
            return content, None

        except ResourceNotFoundError:
            return None, "File not found in Azure Blob"
        except AzureError as e:
            return None, f"Azure Blob error: {str(e)}"
        except Exception as e:
            return None, f"Unexpected Azure Blob error: {str(e)}"

    def generate_presigned_url(self, file_path: str, expiration: int = 3600) -> Tuple[Optional[str], Optional[str]]:
        """
        Generate pre-signed URL for file download

        Args:
            file_path: Relative path for the file
            expiration: URL expiration time in seconds (default: 1 hour)

        Returns:
            Tuple of (url: Optional[str], error_message: Optional[str])
        """
        if self.storage_type == "S3":
            return self._generate_s3_presigned_url(file_path, expiration)
        elif self.storage_type == "AZURE_BLOB":
            return self._generate_azure_presigned_url(file_path, expiration)
        else:
            # For local storage, return the file path (no pre-signed URL needed)
            return file_path, None

    def _generate_s3_presigned_url(self, file_path: str, expiration: int) -> Tuple[Optional[str], Optional[str]]:
        """Generate S3 pre-signed URL"""
        try:
            import boto3
            from botocore.exceptions import ClientError

            # Create S3 client
            s3_client = boto3.client(
                's3',
                region_name=self.customer.s3_region,
                aws_access_key_id=self.customer.s3_access_key_id,
                aws_secret_access_key=self.customer.s3_secret_access_key
            )

            # Construct S3 key
            s3_key = file_path
            if self.customer.s3_prefix:
                s3_key = f"{self.customer.s3_prefix.rstrip('/')}/{file_path}"

            # Generate pre-signed URL
            url = s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.customer.s3_bucket_name,
                    'Key': s3_key
                },
                ExpiresIn=expiration
            )

            return url, None

        except Exception as e:
            error_msg = f"Failed to generate S3 pre-signed URL: {str(e)}"
            logger.error(error_msg)
            return None, error_msg

    def _generate_azure_presigned_url(self, file_path: str, expiration: int) -> Tuple[Optional[str], Optional[str]]:
        """Generate Azure Blob SAS URL"""
        try:
            from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions
            from datetime import datetime, timedelta

            # Create blob service client
            blob_service_client = BlobServiceClient.from_connection_string(
                self.customer.azure_connection_string
            )

            # Construct blob name
            blob_name = file_path
            if self.customer.azure_prefix:
                blob_name = f"{self.customer.azure_prefix.rstrip('/')}/{file_path}"

            # Extract account name and key from connection string
            conn_parts = dict(item.split('=', 1) for item in self.customer.azure_connection_string.split(';') if '=' in item)
            account_name = conn_parts.get('AccountName')
            account_key = conn_parts.get('AccountKey')

            if not account_name or not account_key:
                return None, "Could not extract account credentials from connection string"

            # Generate SAS token
            sas_token = generate_blob_sas(
                account_name=account_name,
                container_name=self.customer.azure_container_name,
                blob_name=blob_name,
                account_key=account_key,
                permission=BlobSasPermissions(read=True),
                expiry=datetime.utcnow() + timedelta(seconds=expiration)
            )

            # Construct full URL
            url = f"https://{account_name}.blob.core.windows.net/{self.customer.azure_container_name}/{blob_name}?{sas_token}"

            return url, None

        except Exception as e:
            error_msg = f"Failed to generate Azure Blob SAS URL: {str(e)}"
            logger.error(error_msg)
            return None, error_msg

    def file_exists(self, file_path: str) -> bool:
        """
        Check if file exists in storage

        Args:
            file_path: Relative path for the file

        Returns:
            True if file exists, False otherwise
        """
        if self.storage_type == "S3":
            exists = self._s3_file_exists(file_path)
            if exists:
                return True
            # Check local fallback if enabled
            if self.fallback_enabled:
                return os.path.exists(file_path)
            return False

        elif self.storage_type == "AZURE_BLOB":
            exists = self._azure_file_exists(file_path)
            if exists:
                return True
            # Check local fallback if enabled
            if self.fallback_enabled:
                return os.path.exists(file_path)
            return False

        else:  # LOCAL
            return os.path.exists(file_path)

    def _s3_file_exists(self, file_path: str) -> bool:
        """Check if file exists in S3"""
        try:
            import boto3
            from botocore.exceptions import ClientError

            s3_client = boto3.client(
                's3',
                region_name=self.customer.s3_region,
                aws_access_key_id=self.customer.s3_access_key_id,
                aws_secret_access_key=self.customer.s3_secret_access_key
            )

            s3_key = file_path
            if self.customer.s3_prefix:
                s3_key = f"{self.customer.s3_prefix.rstrip('/')}/{file_path}"

            s3_client.head_object(Bucket=self.customer.s3_bucket_name, Key=s3_key)
            return True

        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                return False
            logger.error(f"S3 error checking file existence: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error checking S3 file existence: {str(e)}")
            return False

    def _azure_file_exists(self, file_path: str) -> bool:
        """Check if file exists in Azure Blob"""
        try:
            from azure.storage.blob import BlobServiceClient
            from azure.core.exceptions import ResourceNotFoundError

            blob_service_client = BlobServiceClient.from_connection_string(
                self.customer.azure_connection_string
            )

            blob_name = file_path
            if self.customer.azure_prefix:
                blob_name = f"{self.customer.azure_prefix.rstrip('/')}/{file_path}"

            blob_client = blob_service_client.get_blob_client(
                container=self.customer.azure_container_name,
                blob=blob_name
            )

            return blob_client.exists()

        except Exception as e:
            logger.error(f"Unexpected error checking Azure Blob file existence: {str(e)}")
            return False
