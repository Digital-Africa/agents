from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseUpload
import io

class Drive:
    def __init__(self):
        self.service = self.build()

    def build(self):
        SCOPES = ['https://www.googleapis.com/auth/drive']
        SERVICE_ACCOUNT_FILE = 'sa_keys/puppy-executor-key.json'
        # Load credentials from service account file
        creds = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE,
            scopes=SCOPES
        )
        # Build the Drive API service
        service = build('drive', 'v3', credentials=creds)
        return service
    
    def create_folder(self, name, parent_id, permissions_list):
        metadata = {
            'name': name,
            'mimeType': 'application/vnd.google-apps.folder',
            'parents': [parent_id]
        }
        if self.name_not_exists(name, parent_id):
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
        else:
            print(f"Folder {name} already exists at specified path")
            return None

    def get_permissions(self, folder_id):
        response = self.service.permissions().list(
                fileId=folder_id,
                fields='permissions(id,emailAddress,role,type)'
            ).execute()
        return response.get('permissions', [])

    def set_permissions(self, folder_id, email):
        permission = {
                            'type': 'user',        # or 'group', 'domain', 'anyone'
                            'role': "writer",      # or 'reader', 'commenter', 'owner'
                            'emailAddress': email
                        }

        return self.service.permissions().create(
            fileId=folder_id,
            body=permission,
            fields='id',
            sendNotificationEmail=False  # Set to True to notify the user
        ).execute()


    def id_not_exists(self, folder_id):
        try:
            self.service.files().get(fileId=folder_id, fields='id').execute()
            return False  # Folder exists
        except HttpError as e:
            if e.resp.status == 404:
                return True  # Folder does not exist
            else:
                raise  # Propagate other errors
            
    def name_not_exists(self, folder_name, parent_id):
        query = (
            f"name = '{folder_name}' and mimeType = 'application/vnd.google-apps.folder' "
            f"and '{parent_id}' in parents and trashed = false"
        )
        results = self.service.files().list(q=query, fields="files(id, name)").execute()
        folders = results.get('files', [])

        return len(folders) == 0

    def store_notion_file_to_drive(self, notion_file_url: str, filename: str, folder_id: str) -> dict:
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