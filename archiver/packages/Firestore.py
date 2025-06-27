from google.cloud import firestore
from google.oauth2 import service_account
from packages.Notion import Notion
from google.cloud.firestore_v1 import FieldFilter
from packages.Affinity import Affinity
from packages.Slack import get_slack_person_id

class Person:
    """A class to manage person-related operations in Firestore.
    
    This class handles CRUD operations for person documents in Firestore,
    including integration with Notion, Slack, and Affinity IDs.
    """
    
    def __init__(self):
        """Initialize the Person class with Firestore client and collection name."""
        self.collection_name = 'Persons'
        self.client_firebase = self.client()

    def client(self):
        """Create and return a Firestore client instance.
        
        Returns:
            google.cloud.firestore.Client: An authenticated Firestore client.
        """
        key_path = "sa_keys/puppy-executor-key.json"
        credentials = service_account.Credentials.from_service_account_file(key_path)
        client_firestore = firestore.Client(credentials=credentials, project=credentials.project_id, database='memory-bank')
        return client_firestore
    
    def update_collection(self, person):
        """Update or create a person document in Firestore.
        
        Args:
            person (dict): Dictionary containing person information with required keys:
                - notion_id (str): Notion ID of the person
                - email (str): Email address of the person
                Optional keys:
                - slack_id (str): Slack ID of the person
                - affinity_id (str): Affinity ID of the person
        
        Raises:
            ValueError: If required keys (notion_id, email) are missing.
        """
        doc_id = person.get('notion_id')
        email = person.get('email')
        if not doc_id or not email:
            raise ValueError("Person dictionary must contain 'notion_id' and 'email' keys.")
        notion_id = person['notion_id']
        slack_id = person.get('slack_id', get_slack_person_id(email))
        affinity_id = person.get('affinity_id', Affinity().get_affinity_person_id(email))
        
        p = {'notion_id': notion_id, 'email': email, 'slack_id': slack_id, 'affinity_id': affinity_id}
        self.client_firebase.collection(self.collection_name).document(p['notion_id']).set(p, merge=True)
    
    def query_notion_id(self, notion_id):
        """Query a person by their Notion ID.
        
        Args:
            notion_id (str): The Notion ID to search for.
            
        Returns:
            dict or None: Person document if found, None otherwise.
        """
        query = self.client_firebase.collection(self.collection_name).where(filter=FieldFilter('notion_id', '==', notion_id)).get()
        person = [e.to_dict() for e in query]
        return person[0] if person else None
    
    def query_affinity_id(self, affinity_id):
        """Query a person by their Affinity ID.
        
        Args:
            affinity_id (str): The Affinity ID to search for.
            
        Returns:
            dict or None: Person document if found, None otherwise.
        """
        query = self.client_firebase.collection(self.collection_name).where(filter=FieldFilter('affinity_id', '==', affinity_id)).get()
        person = [e.to_dict() for e in query]
        return person[0] if person else None

    def query_slack_id(self, slack_id):
        """Query a person by their Slack ID.
        
        Args:
            slack_id (str): The Slack ID to search for.
            
        Returns:
            dict or None: Person document if found, None otherwise.
        """
        query = self.client_firebase.collection(self.collection_name).where(filter=FieldFilter('slack_id', '==', slack_id)).get()
        person = [e.to_dict() for e in query]
        return person[0] if person else None

    def query_email(self, email):
        """Query a person by their email address.
        
        Args:
            email (str): The email address to search for.
            
        Returns:
            dict or None: Person document if found, None otherwise.
        """
        query = self.client_firebase.collection(self.collection_name).where(filter=FieldFilter('email', '==', email)).get()
        person = [e.to_dict() for e in query]
        return person[0] if person else None
    
    def get_all(self):
        """Retrieve all person documents from Firestore.
        
        Returns:
            list: List of all person documents.
        """
        query = self.client_firebase.collection(self.collection_name).stream()
        person = [e.to_dict() for e in query]
        return person
    
class NotionDatabase:
    """A class to manage Notion database operations in Firestore.
    
    This class handles operations related to Notion databases stored in Firestore.
    """
    
    def __init__(self):
        """Initialize the NotionDatabase class with Firestore client and collection name."""
        self.collection_name = 'NotionDatabases'
        self.client_firestore = self.client()
    
    def client(self):
        """Create and return a Firestore client instance.
        
        Returns:
            google.cloud.firestore.Client: An authenticated Firestore client.
        """
        key_path = "sa_keys/puppy-executor-key.json"
        credentials = service_account.Credentials.from_service_account_file(key_path)
        client_firestore = firestore.Client(credentials=credentials, project=credentials.project_id, database='memory-bank')
        return client_firestore

    def update_collection(self, database):
        """Update or create a Notion database document in Firestore.
        
        Args:
            database (dict): Dictionary containing Notion database information.
        """
        self.client_firestore.collection(self.collection_name).document(database['name']).set(database, merge=True)
    
    def query(self, db_name):
        """Query a Notion database by its name.
        
        Args:
            db_name (str): The name of the database to search for.
            
        Returns:
            dict or None: Database document if found, None otherwise.
        """
        query = self.client_firestore.collection(self.collection_name).where(filter=FieldFilter("name", "==", db_name)).get()
        results = [e.to_dict() for e in query]
        return results[0] if results else None
    
class Memo:
    """A class to manage memo operations in Firestore.
    
    This class handles operations related to memos, including transformation
    of Notion data and storage in Firestore.
    """
    
    def __init__(self, data):
        """Initialize the Memo class with data and Firestore client.
        
        Args:
            data (dict): Raw memo data from Notion.
        """
        self.collection_name = 'Memo'
        self.data = data
        self.reader = Notion().reader
        self.client_firestore = self.client()

    def client(self):
        """Create and return a Firestore client instance.
        
        Returns:
            google.cloud.firestore.Client: An authenticated Firestore client.
        """
        key_path = "sa_keys/puppy-executor-key.json"
        credentials = service_account.Credentials.from_service_account_file(key_path)
        client_firestore = firestore.Client(credentials=credentials, project=credentials.project_id, database='memory-bank')
        return client_firestore
    
    def exists(self):
        """Check if the memo has a self-relation.
        
        Returns:
            bool: True if self-relation exists, False otherwise.
        """
        if self.data['properties']['_self_']['relation']:
            return True
        else:
            return False
    
    def drive_exists(self):
        """Check if the memo has a Drive URL.
        
        Returns:
            bool: True if Drive URL exists, False otherwise.
        """
        if self.data['properties']['Drive']['url']:
            return True
        else:
            return False
    
    def files_media_exists(self):
        """Check if the memo has files or media.
        
        Returns:
            bool: True if files/media exist, False otherwise.
        """
        if self.data['properties']['Files & media']['files']:
            return True
        else:
            return False
    
    def startups_pool_exists(self):
        """Check if the memo has a Startups Pool relation.
        
        Returns:
            bool: True if Startups Pool relation exists, False otherwise.
        """
        if self.data['properties']['Startups Pool']['relation']:
            return True
        else:
            return False
        
    def transform(self):
        """Transform Notion memo data into Firestore document format.
        
        Returns:
            dict: Transformed memo data ready for Firestore storage.
        """
        payload = {}
        payload['id'] = self.data['id']
        payload['created_time'] = self.data['created_time']
        payload['last_edited_time'] = self.data['last_edited_time']
        payload['Memo'] = self.reader.title(self.data['properties']['Memo'])
        payload['external_link'] = self.reader.url(self.data['properties']['external link'])
        payload['id_file'] = self.reader.text(self.data['properties']['id_file'])
        payload['Startups Pool'] = self.reader.relation(self.data['properties']['Startups Pool'])[0]['id'] if self.reader.relation(self.data['properties']['Startups Pool']) else None
        payload['Drive'] = self.reader.url(self.data['properties']['Drive'])
        payload['Tags'] = ','.join([e['name'] for e in self.data['properties']['Tags']['multi_select']]) if self.data['properties']['Tags']['multi_select'] else None
        payload['Date'] = self.data['properties']['Date']['date']
        payload['action_self_'] = self.exists()
        payload['action_drive'] = self.drive_exists()
        payload['action_files_media'] = self.files_media_exists()
        payload['action_startups_pool'] = self.startups_pool_exists()
        payload['creator'] = Person().query_notion_id(self.data['created_by']['id'])
        try:
            payload['files_media'] = ','.join([e['external']['url'] for e in self.data['properties']['Files & media']['files']]) if self.data['properties']['Files & media']['files'] else None
            payload['files_media_source'] = 'external'
        except:
            payload['files_media'] = ','.join([e['file']['url'] for e in self.data['properties']['Files & media']['files']]) if self.data['properties']['Files & media']['files'] else None
            payload['files_media_source'] = 'file'
        return payload
    
    def update_collection(self):
        """Update or create the memo document in Firestore.
        
        Returns:
            google.cloud.firestore.types.WriteResult: Result of the write operation.
        """
        return self.client_firestore.collection(self.collection_name).document(self.data['id']).set(self.transform(), merge=True)

class StorageDriveFolder:
    """A class to manage storage drive operations in Firestore.
    
    This class handles operations related to storage drive documents in Firestore.
    """
    
    def __init__(self):
        """Initialize the StorageDriveFolder class with Firestore client and collection name."""
        self.collection_name = 'StorageDriveFolder'
        self.client_firestore = self.client()
    
    def client(self):
        """Create and return a Firestore client instance.
        
        Returns:
            google.cloud.firestore.Client: An authenticated Firestore client.
        """
        key_path = "sa_keys/puppy-executor-key.json"
        credentials = service_account.Credentials.from_service_account_file(key_path)
        client_firestore = firestore.Client(credentials=credentials, project=credentials.project_id, database='memory-bank')
        return client_firestore

    def update_collection(self, document):
        """Update or create a storage drive document in Firestore.
        
        Args:
            object (dict): Dictionary containing storage drive information.
        """
        self.client_firestore.collection(self.collection_name).document().set(document, merge=True)
    
    def query(self, db_name):
        """Query a storage drive document by its name.
        
        Args:
            db_name (str): The name of the storage drive to search for.
            
        Returns:
            dict or None: Storage drive document if found, None otherwise.
        """
        query = self.client_firestore.collection(self.collection_name).where(filter=FieldFilter("name", "==", db_name)).get()
        results = [e.to_dict() for e in query]
        return results[0] if results else None
    
