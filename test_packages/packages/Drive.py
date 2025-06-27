from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseUpload
import io
import os
import requests
import google.auth


class Drive:
    """Google Drive API client wrapper using Google Application Credentials.
    
    This class provides a simplified interface for Google Drive operations
    including folder creation, permission management, and file uploads.
    Uses Google Application Credentials for authentication.
    
    Attributes:
        service: Google Drive API service instance
    """
    
    def __init__(self):
        """Initialize Drive client with Google Application Credentials.
        
        Raises:
            Exception: If authentication fails or service initialization fails
        """
        self.service = self.build()

    def build(self):
        """Build and return Google Drive service using default credentials.
        
        Uses google.auth.default() to get credentials automatically.
        
        Returns:
            Google Drive API service instance
            
        Raises:
            Exception: If authentication fails or service initialization fails
        """
        SCOPES = ['https://www.googleapis.com/auth/drive']
        
        try:
            # Get credentials using Google Auth default
            credentials, _ = google.auth.default(scopes=SCOPES)
            service = build('drive', 'v3', credentials=credentials)
            return service
        except Exception as e:
            error_msg = f"Failed to authenticate with Google Drive: {e}"
            raise Exception(error_msg)
    
    def create_folder(self, name, parent_id, permissions_list):
        """Create a folder in Google Drive with specified permissions.
        
        Args:
            name (str): Name of the folder to create
            parent_id (str): ID of the parent folder
            permissions_list (list): List of email addresses to grant permissions to
            
        Returns:
            dict: Folder information including ID, URL, and permissions
        """
        metadata = {
            'name': name,
            'mimeType': 'application/vnd.google-apps.folder',
            'parents': [parent_id]
        }
        folder_tiers = self.name_not_exists(name, parent_id)
        if folder_tiers:
            drive_document = folder_tiers[0]
            return {
                    'folder_name': name,
                    'folder_id': drive_document['id'],
                    'parent_id': parent_id,
                    'permissions': self.get_permissions(drive_document['id']),
                    'url': f"https://drive.google.com/drive/folders/{drive_document['id']}"
                    }
        else:
            folder = self.service.files().create(body=metadata, fields='id').execute()
            for p in permissions_list:
                self.set_permissions(folder['id'], p)
            return {
                    'folder_name': name,
                    'folder_id': folder['id'],
                    'parent_id': parent_id,
                    'permissions': self.get_permissions(folder['id']),
                    'url': f"https://drive.google.com/drive/folders/{folder['id']}"
                    }

    def get_permissions(self, folder_id):
        """Get list of permissions for a folder.
        
        Args:
            folder_id (str): ID of the folder
            
        Returns:
            list: List of permission objects
        """
        response = self.service.permissions().list(
                fileId=folder_id,
                fields='permissions(id,emailAddress,role,type)'
            ).execute()
        return response.get('permissions', [])

    def set_permissions(self, folder_id, email):
        """Set permissions for a user on a folder.
        
        Args:
            folder_id (str): ID of the folder
            email (str): Email address of the user to grant permissions to
            
        Returns:
            dict: Permission response from Google Drive API
        """
        permission = {
                            'type': 'user',        # or 'group', 'domain', 'anyone'
                            'role': 'writer',      # or 'reader', 'commenter', 'owner'
                            'emailAddress': email
                        }

        response = self.service.permissions().create(
            fileId=folder_id,
            body=permission,
            fields='id',
            sendNotificationEmail=False  # Set to True to notify the user
        ).execute()
        return response

    def id_not_exists(self, folder_id):
        """Check if a folder ID exists.
        
        Args:
            folder_id (str): ID of the folder to check
            
        Returns:
            bool: True if folder does not exist, False if it exists
        """
        try:
            self.service.files().get(fileId=folder_id, fields='id').execute()
            return False  # Folder exists
        except HttpError as e:
            if e.resp.status == 404:
                return True  # Folder does not exist
            else:
                raise  # Propagate other errors
            
    def name_not_exists(self, folder_name, parent_id):
        """Check if a folder with the given name exists in the parent folder.
        
        Args:
            folder_name (str): Name of the folder to check
            parent_id (str): ID of the parent folder
            
        Returns:
            list: List of matching folders (empty if none found)
        """
        query = (
            f"name = '{folder_name}' and mimeType = 'application/vnd.google-apps.folder' "
            f"and '{parent_id}' in parents and trashed = false"
        )
        results = self.service.files().list(q=query, fields="files(id, name)").execute()
        folders = results.get('files', [])

        return folders

    def store_notion_file_to_drive(self, notion_file_url: str, filename: str, folder_id: str) -> dict:
        """Download a file from Notion and upload it to Google Drive.
        
        Args:
            notion_file_url (str): URL of the file in Notion
            filename (str): Name to give the file in Google Drive
            folder_id (str): ID of the Google Drive folder to upload to
            
        Returns:
            dict: Upload response from Google Drive API
            
        Raises:
            requests.RequestException: If file download fails
            Exception: If upload fails
        """
        # Step 1: Download the file
        headers = {
                    "User-Agent": "Mozilla/5.0"
                }
        response = requests.get(notion_file_url, headers=headers)
        response.raise_for_status()

        file_data = io.BytesIO(response.content)

        file_metadata = {
            'name': filename,
            'parents': [folder_id]
        }
        media = MediaIoBaseUpload(file_data, mimetype=response.headers.get("Content-Type", "application/octet-stream"))

        uploaded = self.service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, name, webViewLink, mimeType'
        ).execute()

        return uploaded