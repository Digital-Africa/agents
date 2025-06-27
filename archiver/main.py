import requests
from typing import Dict, Any
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.cloud import firestore
from datetime import datetime
from packages.Logging import CloudLogger

# Initialize logger with more descriptive name
logger = CloudLogger("GDrive Archive")

# Initialize Firestore client
db = firestore.Client()

def archiver(request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process and archive files from request to Google Drive and store metadata in Firestore.
    
    This function handles the following workflow:
    1. Fetches file data from the API
    2. Downloads the specified file
    3. Uploads the file to Google Drive using service account credentials
    4. Stores file metadata in Firestore
    
    Args:
        request (Dict[str, Any]): The incoming request data containing file information
            Expected keys:
            - name: Name of the file to be archived
            - file: Dictionary containing file details including URL
            - request_id: Unique identifier for the request
    
    Returns:
        Dict[str, Any]: Response containing the status of the archiving operation
            Expected keys:
            - status: Success/failure status
            - file_id: Google Drive file ID (on success)
            - error: Error message (on failure)
    
    Raises:
        requests.RequestException: If there are issues with API requests
        Exception: For any unexpected errors during processing
    """
    try:
        request_id = request.get("request_id", "unknown")
        logger.info("Starting files request processing", extra={
            "request_id": request_id,
            "file_name": request.get("name", "unknown")
        })
        
        # Make API request with proper error handling
        try:
            logger.debug("Fetching file data", extra={
                "endpoint": "files_api",  # Replace with actual endpoint
                "request_type": "GET"
            })
            data = requests.get()  # Replace with actual endpoint
            file = data.json()
            file.raise_for_status()  # Raise exception for bad status codes
            logger.debug("Successfully fetched file data", extra={
                "status_code": data.status_code,
                "response_size": len(data.content)
            })
        except requests.RequestException as e:
            logger.error("Failed to fetch file data", extra={
                "error": str(e),
                "status_code": getattr(e.response, 'status_code', None),
                "endpoint": "files_api"  # Replace with actual endpoint
            })
            raise
            
        # Process the response
        logger.debug("Processing file data", extra={
            "file_name": file.get('name'),
            "file_size": len(file.get('file', {}).get('url', ''))
        })
        file_name = file['name']
        file_url = file['file']['url']
        
        # Download the file
        logger.info("Downloading file", extra={
            "file_name": file_name,
            "file_url": file_url
        })
        r = requests.get(file_url)
        with open(file_name, "wb") as f:
            f.write(r.content)
        logger.debug("File downloaded successfully", extra={
            "file_size": len(r.content),
            "file_name": file_name
        })

        logger.info("Initializing Google Drive service")
        creds = service_account.Credentials.from_service_account_file(
            'sa_keys/puppy-executor-key.json',
            scopes=["https://www.googleapis.com/auth/drive.file"],
        )
        drive_service = build("drive", "v3", credentials=creds)
        logger.debug("Google Drive service initialized successfully")

        # Upload to Google Drive
        file_metadata = {
            "name": file_name,
            "parents": [folder_id]
        }
        logger.info("Uploading file to Google Drive", extra={
            "file_name": file_name,
            "folder_id": folder_id
        })
        media = MediaFileUpload(file_name, resumable=True)
        response = drive_service.files().create(
            body=file_metadata, 
            media_body=media, 
            supportsAllDrives=True, 
            fields="id"
        ).execute()
        
        logger.info("Successfully processed files request", extra={
            "file_id": response.get("id"),
            "file_name": file_name,
            "folder_id": folder_id
        })
        return response
        
    except Exception as e:
        logger.error("Unexpected error in files processing", extra={
            "error": str(e),
            "error_type": type(e).__name__,
            "file_name": file_name if 'file_name' in locals() else None,
            "request_id": request.get("request_id", "unknown")
        })
        raise


