import requests
import json
from packages.Capsule import CapsuleNotion
from packages.SecretAccessor import SecretAccessor
from packages.Logging import CloudLogger
from packages.Notion import Notion
from packages.storage import GCSStorage

class kbis:
    """
    A class to handle the kbis process for startups.
    
    This class manages the retrieval, storage, and documentation of startup kbiss
    in both Google Cloud Storage and Notion databases. It handles file downloads from
    Satori, uploads to GCS, and creates corresponding Notion pages with metadata.
    
    Attributes:
        data (dict): Startup information dictionary
        service_account (str): Path to the service account key file
        database (str): Notion database ID for kbiss
        icon (str): URL for the Notion page icon
        startups_pool (str): Notion database ID for startups pool
        bucket_name (str): GCS bucket name for file storage
        writer (NotionWriter): Notion writer instance for page creation
        childwriter (NotionChildWriter): Notion writer instance for page content
        tags (list): List of tags for the kbis
        id_file (str): ID of the kbis file
        not_exists (bool): Flag indicating if the record exists
        blob_meta (dict): Metadata for the stored file
        match_startups_pool (str): ID of the matching startup in the pool
    """
    def __init__(self, startup):
        self.logger = CloudLogger(__name__)
        self.data = json.loads(startup)
        self.logger.info("Initializing kbis for startup", extra={"startup_id": self.data.get('id')})
        self.service_account = 'sa_keys/puppy-agent-memory-bank-key.json'
        self.database = "96a2609e-e4e4-4a01-ae48-41dd03672bc4"
        self.icon = 'https://www.notion.so/icons/document_blue.svg'
        self.startups_pool = "67853899c6ff4e78aeb2f25b0875b601"
        self.bucket_name = 'agent-memory-bank'
        self.writer = Notion().writer
        self.childwriter = Notion().childwriter
        self.tags = ['kbis']
        self.id_file = self.data['kbis'].split('/')[-1]
        self.not_exists = self._not_exists()
        if self.not_exists:
            self.logger.info("No existing kbis found, proceeding with creation")
            self.blob_meta = self.transform()
            self.match_startups_pool = self.match_satori_id(self.data['id'])[0]['id']
        else:
            self.logger.info("Existing kbis found, skipping creation")

    def get_file_from_satori(self):
        """
        Retrieve a file from the Satori platform.
        
        Authenticates with Satori using service account credentials and downloads
        the specified kbis file.
        
        Returns:
            dict: A dictionary containing:
                - content_type (str): MIME type of the downloaded file
                - file_path (str): Local path where the file was saved
                
        Raises:
            requests.exceptions.RequestException: If the API request fails
        """
        self.logger.info("Attempting to retrieve file from Satori", extra={"file_id": self.id_file})
        email = "puppy-executor@digital-africa-rainbow.iam.gserviceaccount.com"
        base_url = "https://app.fuze.satoripop.io"
        password = SecretAccessor().get_secret('directus')

        try:
            auth_resp = requests.post(f"{base_url}/auth/login", json={
                "email": email,
                "password": password
            })
            auth_resp.raise_for_status()
            access_token = auth_resp.json()['data']['access_token']
            headers = {
                "Authorization": f"Bearer {access_token}"
            }
            
            self.logger.debug("Successfully authenticated with Satori")
            
            file_resp = requests.get(f"{base_url}/assets/{self.id_file}", headers=headers)
            file = requests.get(f"{base_url}/files/{self.id_file}", headers=headers)
            
            file_type = file.json()['data']['type']
            filename = file.json()['data']['title']

            with open(f"{filename}", "wb") as f:
                f.write(file_resp.content)
                
            self.logger.info("File downloaded successfully", extra={
                "filename": filename,
                "file_type": file_type
            })
            
            return {'content_type': file_type, 'file_path': filename}
            
        except requests.exceptions.RequestException as e:
            self.logger.error("Failed to retrieve file from Satori", extra={
                "error": str(e),
                "file_id": self.id_file
            })
            raise

    def store_to_gcs(self):
        """
        Store the kbis file to Google Cloud Storage.
        
        Downloads the file from Satori and uploads it to GCS, making it publicly
        accessible. The file is stored in a path structure based on the startup ID.
        
        Returns:
            dict: A dictionary containing:
                - content_type (str): MIME type of the file
                - file_path (str): Original file path
                - destination_blob_name (str): Path in GCS
                - public_url (str): Publicly accessible URL of the file
                
        Raises:
            Exception: If file upload to GCS fails
        """
        self.logger.info("Starting GCS storage process")
        try:
            blob_meta = self.get_file_from_satori()
            blob_meta['destination_blob_name'] = f"{self.data['id']}/{blob_meta['file_path']}"
            gcs_params = {'bucket_name': self.bucket_name, 'service_account_path': self.service_account}
            
            self.logger.debug("Uploading file to GCS", extra={
                "destination": blob_meta['destination_blob_name'],
                "bucket": self.bucket_name
            })
            
            response = GCSStorage(**gcs_params).save_file(**blob_meta)
            blob = response['blob']
            blob.make_public()
            blob_meta['public_url'] = blob.public_url
            
            self.logger.info("File successfully stored in GCS", extra={
                "public_url": blob_meta['public_url']
            })
            
            return blob_meta
            
        except Exception as e:
            self.logger.error("Failed to store file in GCS", extra={
                "error": str(e),
                "startup_id": self.data['id']
            })
            raise

    def _not_exists(self):
        """
        Check if a kbis record already exists in the Notion database.
        
        Queries the Notion database to check for existing records with the same file ID.
        
        Returns:
            bool: True if no matching record exists, False if a record is found
        """
        self.logger.debug("Checking for existing kbis", extra={"file_id": self.id_file})
        filter_ = {
            "property": "id_file",
            "rich_text": {
                "equals": self.id_file
            }
        }

        try:
            match = Notion().pull.query_database(self.database, filter_)
            exists = bool(match['results'])
            self.logger.debug("Database query completed", extra={"exists": exists})
            return not exists
        except Exception as e:
            self.logger.error("Failed to check for existing record", extra={"error": str(e)})
            raise

    def match_satori_id(self, satori_id):
        """
        Find the corresponding Notion page ID for a Satori startup ID.
        
        Args:
            satori_id (str): The Satori platform ID of the startup
            
        Returns:
            list: List of matching records from the startups pool database.
                 Each record contains the Notion page ID and other metadata.
        """
        self.logger.debug("Matching Satori ID to Notion record", extra={"satori_id": satori_id})
        filter_ = {
            "property": "satori_id",
            "rich_text": {
                "equals": satori_id
            }
        }
        
        try:
            match = Notion().pull.query_database(self.startups_pool, filter_)
            match = match['results']
            self.logger.debug("Found matching startup record", extra={
                "match_count": len(match)
            })
            return match
        except Exception as e:
            self.logger.error("Failed to match Satori ID", extra={
                "error": str(e),
                "satori_id": satori_id
            })
            raise

    def transform(self):
        """
        Transform and store the kbis data.
        
        Handles the process of storing the kbis file to GCS and preparing
        its metadata for Notion integration.
        
        Returns:
            dict: Metadata about the stored file including URLs and content type
        """
        self.logger.info("Starting kbis transformation process")
        try:
            blob_meta = self.store_to_gcs()
            self.logger.info("Transformation completed successfully")
            return blob_meta
        except Exception as e:
            self.logger.error("Transformation failed", extra={"error": str(e)})
            raise

    def build(self):
        """
        Build the Notion page structure for the kbis.
        
        Creates the properties and content structure for a new Notion page,
        including title, relations, tags, and embedded file.
        
        Returns:
            dict: A dictionary containing:
                - properties (dict): Notion page properties
                - children (list): Notion page content blocks
        """
        self.logger.info("Building Notion page structure")
        try:
            url = self.blob_meta['public_url']
            properties = dict()
            properties['Memo'] = self.writer.title(f"{self.data['name']} - kbis")
            properties['id_file'] = self.writer.text(self.id_file)
            properties['Startups Pool'] = self.writer.relation(self.match_startups_pool)
            properties['Tags'] = self.writer.multiselect(self.tags)
            properties['Files & media'] = self.writer.embed_file(title=f"{self.data['name']} - kbis", url=url)
            children = [self.childwriter.paragraph(f"This is the kbis {self.data['name']}"), self.childwriter.embed_file(url)]
            
            self.logger.debug("Notion page structure built successfully", extra={
                "startup_name": self.data['name']
            })
            
            return {'properties': properties, 'children': children}
        except Exception as e:
            self.logger.error("Failed to build Notion page structure", extra={"error": str(e)})
            raise

    def run(self):
        """
        Execute the kbis record creation process.
        
        Checks for existing records and creates a new Notion page if none exists.
        The process includes file storage in GCS and metadata creation in Notion.
        
        Returns:
            dict: A status dictionary containing:
                - status (str): 'success', 'error', or 'info'
                - message (str): Description of the operation result
        """
        self.logger.info("Starting kbis creation process")
        try:
            if self.not_exists:
                notion_build = self.build()
                params = { 
                    'database': self.database,
                    'icon': self.icon,
                    'properties': notion_build['properties'],
                    'children': notion_build['children']
                }
                
                self.logger.debug("Creating Notion page", extra={
                    "database": self.database,
                    "startup_name": self.data['name']
                })
                
                response = CapsuleNotion(**params).enqueue()
                
                if response:
                    self.logger.info("kbis creation queued successfully")
                    return {"status": "success", "message": "kbis record queued for creation"}
                else:
                    self.logger.error("Failed to queue kbis creation")
                    return {"status": "error", "message": "Failed to queue kbis record"}
            else:
                self.logger.info("kbis already exists, skipping creation")
                return {"status": "info", "message": "kbis record already exists"}
                
        except Exception as e:
            self.logger.error("kbis creation process failed", extra={"error": str(e)})
            return {"status": "error", "message": f"Process failed: {str(e)}"}
