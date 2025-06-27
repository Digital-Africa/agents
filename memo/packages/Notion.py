"""
A comprehensive Notion API integration module.

This module provides functionality to:
1. Read and write Notion page properties
2. Create and update Notion pages
3. Query Notion databases
4. Manage Notion API interactions
5. Handle worker queues for batch operations
6. Manage database bindings and references

Example:
    >>> notion = Notion()
    >>> # Create a new page
    >>> properties = {
    ...     "Name": notion.writer.title("My Page"),
    ...     "Status": notion.writer.select("Active")
    ... }
    >>> notion.push.create_page(properties, database_id="your-db-id")
"""

import os
import requests
import json
from datetime import datetime
from typing import Dict, List, Union, Any, Optional
from packages.storage import GCSStorage
from packages.SecretAccessor import SecretAccessor

class NotionAPI:
    """
    Base class for Notion API operations.
    
    Handles authentication and common API operations.
    """
    
    def __init__(self):
        """Initialize the Notion API client."""
        self.token = SecretAccessor().get_secret('NOTION')
        self.headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json',
            'Notion-Version': '2022-06-28'
        }
        self.base_url = 'https://api.notion.com/v1'

class Context:
    """
    Context class for storing database IDs and other context-specific information.
    """
    def get_database_ids(self):
        database_ids = {}
        #Zones    
        database_ids['zone_invest'] = "fe5715570ac747a4aa5452cc3cc9e628"
        database_ids['startups_pool'] = "67853899c6ff4e78aeb2f25b0875b601"
        database_ids['zone_platform'] = "9c0c831726e34ff99de32607e779d2c3"
        database_ids['zone_communication'] = "1c70fcf3849480caa46bde43c221d665"
        #App Bases
        database_ids['Founders'] = "13619a07ff444d05bbee168b31ff7260"
        database_ids['Memo'] = "96a2609ee4e44a01ae4841dd03672bc4"
        database_ids['Vote'] = "3d608e408114403d8cf97c4e1a0e7675"
        #App Bases - references
        database_ids['internal_team'] = "550eb00f314f4f20a3ffd2cb9f5504de"
        database_ids['Mapverse'] = "c4c8efef870e43c298cbd6344b8fb739"
        #App Bases - Affinity
        database_ids['lists'] = '1580fcf38494809e99d8cad050fafa8b'
        database_ids['entities'] = '1880fcf38494800fba43c14e5c84d33f'
        database_ids['opportunities'] = '19d0fcf384948088a1d1d9f23bd7630d'
        database_ids['memo'] = '1890fcf38494800183f1e688d34ca109'
        database_ids['meetings'] = '1990fcf3849480c4ac94dd4f7dc9c413'
        #App Bases    
        database_ids['CONTRACTS'] = "1b50fcf38494801e843cda14be531c4a"
        database_ids['TRANSACTIONS'] = "1b50fcf38494801e843cda14be531c4a"
        return database_ids


class NotionQuery:
    """
    Query class for querying the database.
    """
    def __init__(self,database, query):
        self.context = Context()
        self.database = database
        self.query = query
        self.query_lib = self.get_query_lib()
        
    def get_query_lib(self):
        """
        Get the query library.
        """
        query_lib = {}
        query_lib['token_list'] = {
                                    "or": [
                                        {
                                            "property": "Type",
                                            "select": {
                                                "equals": "Aave"
                                            }
                                        },
                                        {
                                            "property": "Type",
                                            "select": {
                                                "equals": "Silo"
                                            }
                                        },
                                        {
                                            "property": "Type",
                                            "select": {
                                                "equals": "token"
                                            }
                                        }
                                        ]
                                    }
        return query_lib
 
    def run(self):
        """
        Run a query on the database.
        """
        databases = Context().get_database_ids()        
        query = Notion().pull.query_database(databases[self.database],self.query_lib[self.query])
        return query['results']


class NotionReader:
    """
    A utility class for reading and parsing Notion API responses.
    
    This class provides methods to extract different types of data from
    Notion API responses into Python-native formats.
    """
    
    def __init__(self):
        """Initialize the NotionReader."""
        pass

    def title(self, content: Dict) -> str:
        """Extract title content from Notion response."""
        return content['title'][0]['text']['content']

    def text(self, content: Dict) -> str:
        """Extract rich text content from Notion response."""
        return content['rich_text'][0]['text']['content']

    def select(self, content: Dict) -> str:
        """Extract select option name from Notion response."""
        return content['select']['name']

    def page_id(self, content: Dict) -> str:
        """Extract page ID from Notion response."""
        return content['page_id']

    def multiselect(self, content: Dict) -> List[str]:
        """Extract multi-select options from Notion response."""
        return [e['name'].replace(' ', '') for e in content['multi_select']]

    def single_person(self, content: Dict) -> str:
        """Extract single person ID from Notion response."""
        return content['people'][0]['id']

    def multiple_persons(self, content: Dict) -> List[str]:
        """Extract multiple person IDs from Notion response."""
        return [element['id'] for element in content['people']]

    def checkbox(self, content: Dict) -> bool:
        """Extract checkbox state from Notion response."""
        return content['checkbox']

    def relation(self, content: Dict) -> List[Dict]:
        """Extract relation data from Notion response."""
        return content['relation']

    def formula(self, content: Dict) -> str:
        """Extract formula result from Notion response."""
        return content['formula']['string']

    def rollup(self, content: Dict) -> str:
        """Extract rollup data from Notion response."""
        return [[i['plain_text'] for i in k['rich_text']] 
                for k in content['rollup']['array']][0][0]

    def email(self, content: Dict) -> str:
        """Extract email from Notion response."""
        return content['email']

    def url(self, content: Dict) -> str:
        """Extract URL from Notion response."""
        return content['url']

    def number(self, content: Dict) -> float:
        """Extract number from Notion response."""
        return content['number']


class NotionWriter:
    """
    A utility class for creating Notion API-compatible property values.
    
    This class provides methods to format different types of data into the proper
    structure required by the Notion API for creating or updating page properties.
    """
    
    def __init__(self):
        """Initialize the NotionWriter."""
        pass

    def title(self, content: str) -> Dict:
        """Create a Notion title property value."""
        return {
            'title': [{
                'text': {
                    'content': content
                }
            }]
        }

    def text(self, content: Union[str, Any]) -> Dict:
        """Create a Notion rich text property value."""
        return {
            'rich_text': [{
                'text': {
                    'content': str(content)
                }
            }]
        }

    def datetime(self, content: str) -> Dict:
        """Create a Notion date property value."""
        return {
            'date': {
                'start': content,
                'end': None
            }
        }

    def number(self, content: Union[int, float]) -> Dict:
        """Create a Notion number property value."""
        return {'number': float(content)}

    def select(self, content: str) -> Dict:
        """Create a Notion select property value."""
        return {
            'select': {
                'name': content
            }
        }

    def multiselect(self, content: List[str]) -> Dict:
        """Create a Notion multi-select property value."""
        return {
            'multi_select': [
                {'name': name} for name in content
            ]
        }

    def url(self, content: str) -> Dict:
        """Create a Notion URL property value."""
        return {'url': content}

    def single_person(self, content: str) -> Dict:
        """Create a Notion people property value for a single user."""
        return {
            'people': [{
                'object': 'user',
                'id': content
            }]
        }

    def multiple_person(self, content: List[str]) -> Dict:
        """Create a Notion people property value for multiple users."""
        return {
            'people': [
                {
                    'object': 'user',
                    'id': person
                }
                for person in content
            ]
        }

    def checkbox(self, content: bool) -> Dict:
        """Create a Notion checkbox property value."""
        return {'checkbox': content}

    def relation(self, content: Union[str, List[str]]) -> Dict:
        """Create a Notion relation property value."""
        if isinstance(content, str):
            content = [content]
        return {
            'relation': [
                {'id': c} for c in content
            ]
        }

    def embed_file(self, title: str, url: str) -> Dict:
        """Create a Notion file property value."""
        return {
                    "files": [
                        {
                            "type": "external",
                            "name": title,
                            "external": {
                                "url": url
                            }
                        }
                    ]
                }

class NotionChildrenWriter:
    """
    A utility class for creating Notion API-compatible property values.
    
    This class provides methods to format different types of data into the proper
    structure required by the Notion API for creating or updating children page properties.
    """
    def paragraph(self, content: str) -> Dict:
        return {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                                    "rich_text": [{ "type": "text", "text": { "content": content } }]
                                 }
                    }
    def embed_file(self, url: str) -> Dict:
        return {
                    "object": "block",
                    "type": "file",
                    "file": {
                        "type": "external",
                        "external": {
                            "url": url
                        }
                    }
                }
    
    
class NotionPusher(NotionAPI):
    """
    Class for pushing data to Notion.
    
    Handles creating, updating, and deleting Notion pages with worker queue support.
    """
    
    def __init__(self, nb_worker: int = 4):
        """Initialize the NotionPusher with worker configuration."""
        super().__init__()
        self.nb_worker = nb_worker

    def create_page(self, properties: Dict, database_id: str) -> Dict:
        """Create a new Notion page."""
        body = {
            'parent': {'database_id': database_id},
            'properties': properties
        }
        response = requests.post(
            self.base_url + '/pages',
            headers=self.headers,
            json=body
        )
        return response.json()

    def update_page(self, page_id: str, properties: Dict) -> Dict:
        """Update an existing Notion page."""
        url = f"{self.base_url}/pages/{page_id}"
        body = {'properties': properties}
        response = requests.patch(url, headers=self.headers, json=body)
        return response.json()

    def delete_page(self, page_id: str) -> Dict:
        """Archive (soft delete) a Notion page."""
        url = f"{self.base_url}/pages/{page_id}"
        data = {"archived": True}
        response = requests.patch(url, headers=self.headers, json=data)
        return response.json()
    
    def push_to_notion(self, body: Dict, page_id: Optional[str] = None) -> requests.Response:
        """Push data to Notion with optional page ID for updates."""
        if page_id is None:
            return requests.post(self.base_url + '/pages', headers=self.headers, json=body)
        else:
            return requests.patch(f"{self.base_url}/pages/{page_id}", headers=self.headers, json=body)



class NotionPuller(NotionAPI):
    """
    Class for pulling data from Notion.
    
    Handles querying Notion databases and retrieving page data.
    """
    
    def __init__(self):
        """Initialize the NotionPuller."""
        super().__init__()

    def bindings(self, database_id: str) -> Dict[str, str]:
        """Get property bindings for a database."""
        meta = self.get_database(database_id)
        return {
            meta['properties'][k]['id']: k
            for k in meta['properties']
        }

    def get_page(self, page_id: str) -> Dict:
        """Get data for a specific Notion page."""
        url = f"{self.base_url}/pages/{page_id}"
        response = requests.get(url, headers=self.headers)
        return response.json()

    def get_database(self, database_id: str) -> Dict:
        """Get metadata for a specific Notion database."""
        url = f"{self.base_url}/databases/{database_id}"
        response = requests.get(url, headers=self.headers)
        return response.json()

    def query_database(self, database_id: str, filter: Optional[Dict] = None) -> Dict:
        """
        Query a Notion database with optional filters and full pagination support.
        
        Args:
            database_id (str): The ID of the database to query
            filter (Optional[Dict]): Optional filter criteria
            
        Returns:
            Dict: Complete query results including all pages
        """
        url = f'{self.base_url}/databases/{database_id}/query'
        body = {'filter': filter} if filter else {}
        
        all_results = []
        has_more = True
        next_cursor = None
        
        while has_more:
            if next_cursor:
                body['start_cursor'] = next_cursor
                
            response = requests.post(url, headers=self.headers, json=body)
            data = response.json()
            all_results.extend(data['results'])
            has_more = data.get('has_more', False)
            next_cursor = data.get('next_cursor')
        
        return {'results': all_results}

    def to_dict(self, database_id: str, columns: List[str]) -> List[Dict]:
        """Convert database query results to a list of dictionaries."""
        def get_results(data: Dict) -> List[Dict]:
            results = []
            for element in data['results']:
                page_id = {
                    'type': 'page_id',
                    'page_id': element['id'].replace('-', '')
                }
                line = element['properties']
                line['page_id'] = page_id
                results.append(line)
            return results

        def request_records(url: str, json_data: Optional[Dict] = None) -> tuple:
            response = requests.post(url, headers=self.headers, json=json_data)
            data = response.json()
            has_more = data.get('has_more')
            next_cursor = data.get('next_cursor')
            results = get_results(data)
            return next_cursor, results, has_more

        url = f'{self.base_url}/databases/{database_id}/query'
        next_cursor, results, has_more = request_records(url)

        while has_more:
            params = {'start_cursor': next_cursor}
            next_cursor, more_results, has_more = request_records(url, json_data=params)
            results.extend(more_results)

        return [
            {k: line[k] for k in line if k in columns}
            for line in results
        ]



class Notion:
    """
    Main Notion integration class.
    
    Combines reading, writing, pushing, and pulling functionality.
    """

    def __init__(self):
        """Initialize the Notion client."""
        self.pull = NotionPuller()
        self.push = NotionPusher()
        self.reader = NotionReader()
        self.writer = NotionWriter()
        self.childwriter = NotionChildrenWriter()

# Export main classes
__all__ = ['Notion', 'NotionReader', 'NotionWriter', 'NotionPusher', 'NotionPuller'] 
