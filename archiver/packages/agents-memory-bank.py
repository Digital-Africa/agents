from packages.storage import GCSStorage

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
    