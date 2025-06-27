
from google.cloud import firestore
from google.oauth2 import service_account
from packages.Notion import Notion
from google.cloud.firestore_v1 import FieldFilter
from packages.Affinity import Affinity
from packages.Slack import get_slack_person_id

class Person:
    def __init__(self):
        self.collection_name = 'Persons'
        self.client_firebase = self.client()

    def client(self):
        key_path = "sa_keys/puppy-executor-key.json"
        credentials = service_account.Credentials.from_service_account_file(key_path)
        client_firestore = firestore.Client(credentials=credentials, project=credentials.project_id, database='memory-bank')
        return client_firestore
    
    def update_collection(self, person):

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
        query = self.client_firebase.collection(self.collection_name).where(filter=FieldFilter('notion_id', '==', notion_id)).get()
        person = [e.to_dict() for e in query]
        return person
    
    def query_affinity_id(self, affinity_id):
        query = self.client_firebase.collection(self.collection_name).where(filter=FieldFilter('affinity_id', '==', affinity_id)).get()
        person = [e.to_dict() for e in query]
        return person

    def query_slack_id(self, slack_id):
        query = self.client_firebase.collection(self.collection_name).where(filter=FieldFilter('slack_id', '==', slack_id)).get()
        person = [e.to_dict() for e in query]
        return person

    def query_email(self, email):
        query = self.client_firebase.collection(self.collection_name).where(filter=FieldFilter('email', '==', email)).get()
        person = [e.to_dict() for e in query]
        return person
    
class NotionDatabase:
    def __init__(self):
        self.collection_name = 'NotionDatabases'
        self.client_firestore = self.client()
    
    def client(self):
        key_path = "sa_keys/puppy-executor-key.json"
        credentials = service_account.Credentials.from_service_account_file(key_path)
        client_firestore = firestore.Client(credentials=credentials, project=credentials.project_id, database='memory-bank')
        return client_firestore

    def update_collection(self, database):
        self.client_firestore.collection(self.collection_name).document(database['name']).set(database, merge=True)
    
    def query(self, db_name):
        query = self.client_firestore.collection(self.collection_name).where(filter=FieldFilter("name", "==", db_name)).get()
        db = [e.to_dict() for e in query][0]
        return db
    
class Memo:
    def __init__(self, data):
        self.collection_name = 'Memo'
        self.data = data
        self.reader = Notion().reader
        self.client_firestore = self.client()

    def client(self):
        key_path = "sa_keys/puppy-executor-key.json"
        credentials = service_account.Credentials.from_service_account_file(key_path)
        client_firestore = firestore.Client(credentials=credentials, project=credentials.project_id, database='memory-bank')
        return client_firestore
    
    def exists(self):
        if self.data['properties']['_self_']['relation']:
            return True
        else:
            return False
    
    def drive_exists(self):
        if self.data['properties']['Drive']['url']:
            return True
        else:
            return False
    
    def files_media_exists(self):
        if self.data['properties']['Files & media']['files']:
            return True
        else:
            return False
    
    def startups_pool_exists(self):
        if self.data['properties']['Startups Pool']['relation']:
            return True
        else:
            return False
        
    def transform(self):
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
        return self.client_firestore.collection(self.collection_name).document(self.data['id']).set(self.transform(), merge=True)

