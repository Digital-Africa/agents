"""
Google Cloud Storage primitive for accessing files.
"""
from google.cloud import storage
import os
from typing import Optional, Union, BinaryIO
from packages.Logging import CloudLogger

logger = CloudLogger("storage")

class Storage:
    def __init__(self, bucket_name: str):
        """
        Initialize the Storage client.

        Args:
            bucket_name (str): The name of the GCS bucket to use
        """
        self.client = storage.Client()
        self.bucket_name = bucket_name
        self.bucket = self.client.bucket(bucket_name)
        logger.info(f"[Storage] Initialized with bucket: {bucket_name}")

    def read_file(self, file_path: str) -> Optional[bytes]:
        """
        Read a file from Google Cloud Storage.

        Args:
            file_path (str): The path to the file in the bucket

        Returns:
            Optional[bytes]: The file content as bytes, or None if the file doesn't exist
        """
        try:
            logger.debug(f"[Storage] Reading file: {file_path}")
            blob = self.bucket.blob(file_path)
            
            if not blob.exists():
                logger.warning(f"[Storage] File not found: {file_path}")
                return None
                
            content = blob.download_as_bytes()
            logger.info(f"[Storage] Successfully read file: {file_path}")
            return content
            
        except Exception as e:
            logger.error(f"[Storage] Error reading file {file_path}: {str(e)}")
            raise

    def write_file(self, file_path: str, content: Union[bytes, str, BinaryIO]) -> bool:
        """
        Write a file to Google Cloud Storage.

        Args:
            file_path (str): The path to write the file to in the bucket
            content (Union[bytes, str, BinaryIO]): The content to write

        Returns:
            bool: True if the write was successful, False otherwise
        """
        try:
            logger.debug(f"[Storage] Writing file: {file_path}")
            blob = self.bucket.blob(file_path)
            
            if isinstance(content, str):
                content = content.encode('utf-8')
            elif isinstance(content, BinaryIO):
                content = content.read()
                
            blob.upload_from_string(content)
            logger.info(f"[Storage] Successfully wrote file: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"[Storage] Error writing file {file_path}: {str(e)}")
            return False

    def delete_file(self, file_path: str) -> bool:
        """
        Delete a file from Google Cloud Storage.

        Args:
            file_path (str): The path to the file in the bucket

        Returns:
            bool: True if the delete was successful, False otherwise
        """
        try:
            logger.debug(f"[Storage] Deleting file: {file_path}")
            blob = self.bucket.blob(file_path)
            
            if not blob.exists():
                logger.warning(f"[Storage] File not found for deletion: {file_path}")
                return False
                
            blob.delete()
            logger.info(f"[Storage] Successfully deleted file: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"[Storage] Error deleting file {file_path}: {str(e)}")
            return False

    def list_files(self, prefix: str = "") -> list:
        """
        List files in the bucket with an optional prefix.

        Args:
            prefix (str): Optional prefix to filter files

        Returns:
            list: List of file paths
        """
        try:
            logger.debug(f"[Storage] Listing files with prefix: {prefix}")
            blobs = self.bucket.list_blobs(prefix=prefix)
            files = [blob.name for blob in blobs]
            logger.info(f"[Storage] Found {len(files)} files with prefix: {prefix}")
            return files
            
        except Exception as e:
            logger.error(f"[Storage] Error listing files: {str(e)}")
            return []

    def file_exists(self, file_path: str) -> bool:
        """
        Check if a file exists in the bucket.

        Args:
            file_path (str): The path to the file in the bucket

        Returns:
            bool: True if the file exists, False otherwise
        """
        try:
            logger.debug(f"[Storage] Checking if file exists: {file_path}")
            blob = self.bucket.blob(file_path)
            exists = blob.exists()
            logger.debug(f"[Storage] File {file_path} exists: {exists}")
            return exists
            
        except Exception as e:
            logger.error(f"[Storage] Error checking file existence {file_path}: {str(e)}")
            return False 