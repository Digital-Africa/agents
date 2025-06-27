from typing import List, Optional, Dict, Union
from google.cloud import storage
from google.cloud.storage import Blob
import json
import os
from datetime import datetime
import logging
import pandas as pd
import io
from google.auth import default

class GCSStorage:
    """Google Cloud Storage client wrapper for simplified file operations.
    
    This class provides a high-level interface for common Google Cloud Storage operations
    including reading, writing, copying, and listing files. It uses Google Application
    Credentials for authentication.
    
    Attributes:
        project (str): Google Cloud project ID
        client (storage.Client): Authenticated Google Cloud Storage client
        bucket (storage.Bucket): Reference to the specified GCS bucket
    """
    
    def __init__(self, bucket_name: str, project_id: str = 'digital-africa-rainbow'):
        """Initialize GCS storage client with default credentials.
        
        Args:
            bucket_name (str): Name of the GCS bucket to operate on
            project_id (str, optional): Google Cloud project ID. 
                Defaults to 'digital-africa-rainbow'.
                
        Raises:
            Exception: If authentication fails or bucket doesn't exist
        """
        self.project = project_id
        self.client = self.get_client()
        self.bucket = self.client.bucket(bucket_name)
        
    def get_client(self) -> storage.Client:
        """Create and return an authenticated Google Cloud Storage client.
        
        Uses Google Application Credentials for authentication.
        
        Returns:
            storage.Client: Authenticated Google Cloud Storage client
            
        Raises:
            Exception: If authentication fails
        """
        creds, _ = default()
        return storage.Client(credentials=creds, project=self.project)
            
    def read_file(self, blob_name: str) -> Optional[bytes]:
        """Read a file from Google Cloud Storage.
        
        Downloads the entire content of a blob as bytes.
        
        Args:
            blob_name (str): Name/path of the blob in the bucket
            
        Returns:
            Optional[bytes]: File content as bytes if successful, None if failed
            
        Example:
            >>> storage = GCSStorage('my-bucket')
            >>> content = storage.read_file('path/to/file.txt')
            >>> if content:
            ...     print(content.decode('utf-8'))
        """
        try:
            blob = self.bucket.blob(blob_name)
            return blob.download_as_bytes()
        except Exception as e:
            logging.error(f"Error reading file {blob_name}: {e}")
            return None
            
    def write_file(self, blob_name: str, content: bytes, content_type: str = None) -> bool:
        """Write content to a file in Google Cloud Storage.
        
        Uploads bytes content to a blob in the bucket.
        
        Args:
            blob_name (str): Name/path where to store the file in the bucket
            content (bytes): Binary content to write
            content_type (str, optional): MIME type of the content (e.g., 'text/plain')
            
        Returns:
            bool: True if successful, False otherwise
            
        Example:
            >>> storage = GCSStorage('my-bucket')
            >>> content = b'Hello, World!'
            >>> success = storage.write_file('hello.txt', content, 'text/plain')
        """
        try:
            blob = self.bucket.blob(blob_name)
            blob.upload_from_string(
                content,
                content_type=content_type
            )
            return True
        except Exception as e:
            logging.error(f"Error writing file {blob_name}: {e}")
            return False
            
    def list_new_files(self, prefix: str = "") -> List[str]:
        """List all files in the bucket with optional prefix filtering.
        
        Args:
            prefix (str, optional): Prefix to filter files. Only files whose names
                start with this prefix will be returned. Defaults to "" (all files).
            
        Returns:
            List[str]: List of blob names matching the prefix
            
        Example:
            >>> storage = GCSStorage('my-bucket')
            >>> files = storage.list_new_files('data/')
            >>> print(f"Found {len(files)} files in data/ directory")
        """
        try:
            blobs = self.bucket.list_blobs(prefix=prefix)
            new_files = []
            
            for blob in blobs:
                new_files.append(blob.name)
            return new_files
        
        except Exception as e:
            logging.error(f"Error listing new files: {e}")
            return []

    def read_excel(self, blob_name: str, **kwargs) -> Optional[pd.DataFrame]:
        """Read an Excel file from GCS and return it as a pandas DataFrame.
        
        Downloads an Excel file from GCS and loads it into a pandas DataFrame.
        Supports all pandas.read_excel() parameters.
        
        Args:
            blob_name (str): Name/path of the Excel file in the bucket
            **kwargs: Additional arguments to pass to pandas.read_excel()
                Common options include:
                - sheet_name: Name or index of sheet to read
                - header: Row number to use as column names
                - skiprows: Number of rows to skip
                - usecols: Columns to read
                - dtype: Data types for columns
                
        Returns:
            Optional[pd.DataFrame]: DataFrame containing the Excel data if successful, 
                None if failed
            
        Example:
            >>> storage = GCSStorage('my-bucket')
            >>> df = storage.read_excel('data/sales.xlsx', sheet_name='Sheet1')
            >>> if df is not None:
            ...     print(df.head())
        """
        try:
            content = self.read_file(blob_name)
            if content is None:
                return None
                
            # Create a BytesIO object from the content
            excel_data = io.BytesIO(content)
            
            # Read the Excel file into a DataFrame
            df = pd.read_excel(excel_data, **kwargs)
            return df
            
        except Exception as e:
            logging.error(f"Error reading Excel file {blob_name}: {e}")
            return None 

    def copy_file(self, source_blob_name: str, destination_blob_name: str) -> bool:
        """Copy a file within the same bucket.
        
        Creates a copy of the source file at the destination location.
        The original source file is preserved.
        
        Args:
            source_blob_name (str): Name/path of the source file to copy
            destination_blob_name (str): Name/path for the destination file
            
        Returns:
            bool: True if successful, False otherwise
            
        Example:
            >>> storage = GCSStorage('my-bucket')
            >>> success = storage.copy_file('data/input.csv', 'backup/input.csv')
        """
        try:
            # Check if source file exists
            source_blob = self.bucket.blob(source_blob_name)
            if not source_blob.exists():
                logging.error(f"Source file {source_blob_name} does not exist")
                return False
                
            # Copy the file (source file is preserved)
            new_blob = self.bucket.copy_blob(
                source_blob,
                self.bucket,
                destination_blob_name
            )
            return True
        except Exception as e:
            logging.error(f"Error copying file from {source_blob_name} to {destination_blob_name}: {e}")
            return False 

    def save_file(self, file_path: str, destination_blob_name: str, content_type: str = None) -> Dict[str, Union[bool, str]]:
        """Save a local file to Google Cloud Storage.
        
        Uploads a local file to a specific location in the GCS bucket.
        
        Args:
            file_path (str): Local path to the file to be uploaded
            destination_blob_name (str): Name/path where the file should be stored in the bucket
            content_type (str, optional): MIME type of the file (e.g., 'application/json')
            
        Returns:
            Dict[str, Union[bool, str]]: Dictionary with status information:
                - status (bool): True if successful, False otherwise
                - message (str): Success or error message
                - blob (storage.Blob, optional): Blob object if successful
                
        Example:
            >>> storage = GCSStorage('my-bucket')
            >>> result = storage.save_file('local/data.json', 'remote/data.json', 'application/json')
            >>> if result['status']:
            ...     print(f"File uploaded: {result['message']}")
        """
        try:
            # Check if source file exists
            if not os.path.exists(file_path):
                logging.error(f"Source file {file_path} does not exist")
                return {'status': False, 'message': f"Source file {file_path} does not exist"}
                
            # Create a new blob and upload the file
            blob = self.bucket.blob(destination_blob_name)
            blob.upload_from_filename(file_path, content_type=content_type)
            return {'status': True, 'message': f"File saved to {destination_blob_name}",'blob': blob}
        except Exception as e:
            logging.error(f"Error saving file from {file_path} to {destination_blob_name}: {e}")
            return {'status': False, 'message': f"Error saving file from {file_path} to {destination_blob_name}: {e}"}

    def read_json(self, blob_name: str) -> Optional[Dict]:
        """Read and parse a JSON file from Google Cloud Storage.
        
        Downloads a JSON file from GCS and parses it into a Python dictionary.
        
        Args:
            blob_name (str): Name/path of the JSON file in the bucket
            
        Returns:
            Optional[Dict]: Parsed JSON data as dictionary if successful, None if failed
            
        Example:
            >>> storage = GCSStorage('my-bucket')
            >>> data = storage.read_json('config/settings.json')
            >>> if data:
            ...     print(f"API key: {data.get('api_key')}")
        """
        try:
            content = self.read_file(blob_name)
            if content is None:
                return None
                
            # Parse the JSON content
            return json.loads(content.decode('utf-8'))
            
        except json.JSONDecodeError as e:
            logging.error(f"Error parsing JSON from {blob_name}: {e}")
            return None
        except Exception as e:
            logging.error(f"Error reading JSON file {blob_name}: {e}")
            return None 

    def read_csv(self, blob_name: str, **kwargs) -> Optional[pd.DataFrame]:
        """Read a CSV file from GCS and return it as a pandas DataFrame.
        
        Downloads a CSV file from GCS and loads it into a pandas DataFrame.
        Supports all pandas.read_csv() parameters.
        
        Args:
            blob_name (str): Name/path of the CSV file in the bucket
            **kwargs: Additional arguments to pass to pandas.read_csv()
                Common options include:
                - sep: Delimiter to use (default: ',')
                - encoding: File encoding (default: 'utf-8')
                - header: Row number to use as column names
                - index_col: Column to use as index
                - dtype: Data types for columns
                - na_values: Values to treat as NaN
                
        Returns:
            Optional[pd.DataFrame]: DataFrame containing the CSV data if successful, 
                None if failed
            
        Example:
            >>> storage = GCSStorage('my-bucket')
            >>> df = storage.read_csv('data/users.csv', encoding='utf-8', sep=',')
            >>> if df is not None:
            ...     print(f"Loaded {len(df)} rows")
        """
        try:
            content = self.read_file(blob_name)
            if content is None:
                return None
                
            # Create a BytesIO object from the content
            csv_data = io.BytesIO(content)
            
            # Read the CSV file into a DataFrame
            df = pd.read_csv(csv_data, **kwargs)
            return df
            
        except Exception as e:
            logging.error(f"Error reading CSV file {blob_name}: {e}")
            return None 
        
class Reference:
    """Reference paths for commonly used files in the storage bucket.
    
    This class provides centralized access to file paths used across the application.
    All paths are relative to the bucket root.
    """
    
    NotionDatabases = "references/NotionDatabases.json"
    NotionFilters = "references/NotionFilters.json"
    SlackGroups = "references/SlackGroups.json"
    SlackPersons = "references/SlackPersons.json"
    NotionPersons = "references/NotionPersons.json"
    AffinityPersons = "references/AffinityPersons.json"
    Persons = "references/Persons.json"
        
class Operation:
    """Operations class for managing agent memory bank data.
    
    This class provides methods for reading, updating, and publishing data
    to the agent memory bank bucket using Google Application Credentials.
    
    Attributes:
        bucket_name (str): Name of the GCS bucket for agent memory bank
    """
    
    def __init__(self):
        """Initialize the Operation class with agent memory bank configuration."""
        self.bucket_name = 'agent-memory-bank'
    
    def get(self, location: str) -> Dict[str, Union[str, Optional[Dict]]]:
        """Retrieve data from the agent memory bank.
        
        Args:
            location (str): Path to the JSON file in the bucket
            
        Returns:
            Dict[str, Union[str, Optional[Dict]]]: Dictionary containing:
                - location (str): The requested file path
                - result (Optional[Dict]): Parsed JSON data if successful, None if failed
                
        Example:
            >>> op = Operation()
            >>> data = op.get('references/Persons.json')
            >>> if data['result']:
            ...     print(f"Retrieved {len(data['result'])} persons")
        """
        context = {'bucket_name': self.bucket_name}
        params = {'blob_name': location}
        result = GCSStorage(**context).read_json(**params)
        return {
                    'location': location, 
                    'result': result
                }
    
    def update(self, location: str, key: str, val: any) -> None:
        """Update a local JSON file with new key-value pair.
        
        Reads the existing JSON file, updates it with the new key-value pair,
        and writes it back to the local filesystem.
        
        Args:
            location (str): Local path to the JSON file
            key (str): Key to update or add
            val (any): Value to set for the key
            
        Example:
            >>> op = Operation()
            >>> op.update('local/config.json', 'last_update', '2024-01-01')
        """
        try:
            with open(location, 'r') as json_file:
                target = json.load(json_file)

            target[key] = val
        except:
            target = dict()
            target[key] = val
            print(f'file not found at {location}\nCreating a new file')

        # Write the updated JSON back to the file
        with open(location, 'w') as json_file:
            json.dump(target, json_file, indent=4)
    
    def publish(self, location: str) -> None:
        """Publish a local JSON file to the agent memory bank.
        
        Uploads a local JSON file to the agent memory bank bucket.
        
        Args:
            location (str): Local path to the JSON file to publish
            
        Example:
            >>> op = Operation()
            >>> op.publish('local/updated_persons.json')
        """
        context = {'bucket_name': self.bucket_name}
        params = {'file_path': location, 'destination_blob_name': location, 'content_type': "application/json"}
        result = GCSStorage(**context).save_file(**params)
        print(f"gs://{location}", result)
    