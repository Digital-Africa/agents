from typing import List, Optional, Dict, Union
from google.cloud import storage
from google.cloud.storage import Blob
import json
import os
from datetime import datetime
import logging
import pandas as pd
import io

class GCSStorage:
    def __init__(self, bucket_name: str, service_account_path: str, processed_files_path: str = "processed_files.json"):
        """
        Initialize GCS storage client and track processed files.
        
        Args:
            bucket_name (str): Name of the GCS bucket
            service_account_path (str): Path to the service account JSON file
            processed_files_path (str): Local path to store processed files metadata
        """
        self.client = storage.Client.from_service_account_json(service_account_path)
        self.bucket = self.client.bucket(bucket_name)
        self.processed_files_path = processed_files_path
        self.processed_files = self._load_processed_files()
        
    def _load_processed_files(self) -> Dict[str, str]:
        """Load the list of processed files from local storage."""
        try:
            if os.path.exists(self.processed_files_path):
                with open(self.processed_files_path, 'r') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logging.error(f"Error loading processed files: {e}")
            return {}
            
    def _save_processed_files(self):
        """Save the list of processed files to local storage."""
        try:
            with open(self.processed_files_path, 'w') as f:
                json.dump(self.processed_files, f)
        except Exception as e:
            logging.error(f"Error saving processed files: {e}")
            
    def read_file(self, blob_name: str) -> Optional[bytes]:
        """
        Read a file from GCS.
        
        Args:
            blob_name (str): Name of the blob to read
            
        Returns:
            Optional[bytes]: File content if successful, None otherwise
        """
        try:
            blob = self.bucket.blob(blob_name)
            return blob.download_as_bytes()
        except Exception as e:
            logging.error(f"Error reading file {blob_name}: {e}")
            return None
            
    def write_file(self, blob_name: str, content: bytes, content_type: str = None) -> bool:
        """
        Write a file to GCS.
        
        Args:
            blob_name (str): Name of the blob to write
            content (bytes): Content to write
            content_type (str, optional): Content type of the file
            
        Returns:
            bool: True if successful, False otherwise
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
        """
        List new files in the bucket that haven't been processed yet.
        
        Args:
            prefix (str): Optional prefix to filter files
            
        Returns:
            List[str]: List of new blob names
        """
        try:
            blobs = self.bucket.list_blobs(prefix=prefix)
            new_files = []
            
            for blob in blobs:
                if blob.name not in self.processed_files:
                    new_files.append(blob.name)
                    
            return new_files
        except Exception as e:
            logging.error(f"Error listing new files: {e}")
            return []
            
    def mark_as_processed(self, blob_name: str):
        """
        Mark a file as processed.
        
        Args:
            blob_name (str): Name of the blob to mark as processed
        """
        self.processed_files[blob_name] = datetime.now().isoformat()
        self._save_processed_files()
        
    def is_processed(self, blob_name: str) -> bool:
        """
        Check if a file has been processed.
        
        Args:
            blob_name (str): Name of the blob to check
            
        Returns:
            bool: True if processed, False otherwise
        """
        return blob_name in self.processed_files 

    def read_excel(self, blob_name: str, **kwargs) -> Optional[pd.DataFrame]:
        """
        Read an Excel file from GCS and return it as a pandas DataFrame.
        
        Args:
            blob_name (str): Name of the blob to read
            **kwargs: Additional arguments to pass to pandas.read_excel()
            
        Returns:
            Optional[pd.DataFrame]: DataFrame containing the Excel data if successful, None otherwise
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
        """
        Copy a file within the same bucket. The source file is preserved.
        
        Args:
            source_blob_name (str): Name of the source blob to copy
            destination_blob_name (str): Name of the destination blob
            
        Returns:
            bool: True if successful, False otherwise
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

    def save_file(self, file_path: str, destination_blob_name: str, content_type: str = None) -> bool:
        """
        Save a local file to a specific location in the GCS bucket.
        
        Args:
            file_path (str): Local path to the file to be saved
            destination_blob_name (str): Name/path where the file should be saved in the bucket
            content_type (str, optional): Content type of the file
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Check if source file exists
            if not os.path.exists(file_path):
                logging.error(f"Source file {file_path} does not exist")
                return False
                
            # Create a new blob and upload the file
            blob = self.bucket.blob(destination_blob_name)
            blob.upload_from_filename(file_path, content_type=content_type)
            return {'status': True, 'message': f"File saved to {destination_blob_name}",'blob': blob}
        except Exception as e:
            logging.error(f"Error saving file from {file_path} to {destination_blob_name}: {e}")
            return {'status': False, 'message': f"Error saving file from {file_path} to {destination_blob_name}: {e}"}

    def read_json(self, blob_name: str) -> Optional[Dict]:
        """
        Read and parse a JSON file from GCS.
        
        Args:
            blob_name (str): Name of the JSON blob to read
            
        Returns:
            Optional[Dict]: Parsed JSON data if successful, None otherwise
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
        """
        Read a CSV file from GCS and return it as a pandas DataFrame.
        
        Args:
            blob_name (str): Name of the blob to read
            **kwargs: Additional arguments to pass to pandas.read_csv()
                     Common options include:
                     - sep: Delimiter to use (default: ',')
                     - encoding: File encoding (default: 'utf-8')
                     - header: Row number to use as column names
                     - index_col: Column to use as index
                     - dtype: Data types for columns
            
        Returns:
            Optional[pd.DataFrame]: DataFrame containing the CSV data if successful, None otherwise
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
    NotionDatabases = "references/NotionDatabases.json"
    NotionFilters = "references/NotionFilters.json"
    SlackGroups = "references/SlackGroups.json"
    SlackPersons = "references/SlackPersons.json"
    NotionPersons = "references/NotionPersons.json"
    AffinityPersons = "references/AffinityPersons.json"
    Persons = "references/Persons.json"
        
class Operation:
    def __init__(self):
        self.bucket_name = 'agent-memory-bank'
        self.service_account_path = 'sa_keys/puppy-agent-memory-bank-key.json'
    
    def get(self, location):
        context = {'bucket_name': self.bucket_name,'service_account_path': self.service_account_path}
        params = {'blob_name': location}
        result = GCSStorage(**context).read_json(**params)
        return {
                    'location': location, 
                    'result': result
                }
    
    def update(self, location, key, val):
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
    
    def publish(self, location):
        context = {'bucket_name': self.bucket_name,'service_account_path': self.service_account_path}
        params = {'file_path': location, 'destination_blob_name': location, 'content_type': "application/json"}
        result = GCSStorage(**context).save_file(**params)
        print(f"gs://{location}", result)
    