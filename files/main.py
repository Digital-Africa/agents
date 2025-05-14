import requests
from typing import Dict, Any
from packages.Logging import CloudLogger

# Initialize logger with more descriptive name
logger = CloudLogger("storage_files ")

def files(request: Dict[str, Any]) -> Dict[str, Any]:
    context = {'bucket_name': 'fuze-subscriptions','service_account_path': 'sa_keys/puppy-agent-memory-bank-key.json'}
    storage = GCSStorage(**context)
    params = {'prefix': ''}
    blobs = GCSStorage(**context).list_new_files(**params)

    raw_files = set(filter(lambda x: 'processed_files/' not in x, blobs))
    processed_files = set(e.split('/')[1] for e in filter(lambda x: 'processed_files/' in x, blobs))
    queue = raw_files.difference(processed_files)
    startups_files = list(filter(lambda x: 'startups' in x, queue))
    cofounders_files = list(filter(lambda x: 'cofounders' in x, queue))

    for startup_file in startups_files:
        print('send to dispatch')
    for cofounder_file in cofounders_files:
        print('send to dispatch')

    return {'message': 'Files processed'}
