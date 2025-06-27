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
import re
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
        return content['title'][0]['text']['content'] if content['title'] else None

    def text(self, content: Dict) -> str:
        """Extract rich text content from Notion response."""
        return content['rich_text'][0]['text']['content'] if content['rich_text'] else None

    def select(self, content: Dict) -> str:
        """Extract select option name from Notion response."""
        try:
            return content['select']['name']
        except:
            return None

    def page_id(self, content: Dict) -> str:
        """Extract page ID from Notion response."""
        return content['page_id']

    def multiselect(self, content: Dict) -> List[str]:
        """Extract multi-select options from Notion response."""
        try:
            return [e['name'].replace(' ', '') for e in content['multi_select']]
        except: 
            return None

    def single_person(self, content: Dict) -> str:
        """Extract single person ID from Notion response."""
        return content['people'][0]['id'] if content['people'] else None

    def multiple_persons(self, content: Dict) -> List[str]:
        """Extract multiple person IDs from Notion response."""
        try:
            return [element['id'] for element in content['people']]
        except:
            return None

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
    
    def embed_file(self, content: Dict) -> str:
        """Extract file URL from Notion response."""
        try:
            return content['file']['external']['url']
        except:
            return None


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

    def email(self, content: str) -> Dict:
        """Create a Notion email property value."""
        return {
                    "email": content
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
    
    def heading_1(self, content: str) -> Dict:
        return {
            "object": "block",
            "type": "heading_1",
            "heading_1": {
                "rich_text": [{"type": "text", "text": {"content": content}}]
            }
        }
    
    def heading_2(self, content: str) -> Dict:
        return {
            "object": "block",
            "type": "heading_2",
            "heading_2": {
                "rich_text": [{"type": "text", "text": {"content": content}}]
            }
        }
    
    def heading_3(self, content: str) -> Dict:
        return {
            "object": "block",
            "type": "heading_3",
            "heading_3": {
                "rich_text": [{"type": "text", "text": {"content": content}}]
            }
        }
    
    def bulleted_list_item(self, content: str) -> Dict:
        return {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [{"type": "text", "text": {"content": content}}]
            }
        }
    
    def numbered_list_item(self, content: str) -> Dict:
        return {
            "object": "block",
            "type": "numbered_list_item",
            "numbered_list_item": {
                "rich_text": [{"type": "text", "text": {"content": content}}]
            }
        }
    
    def quote(self, content: str) -> Dict:
        return {
            "object": "block",
            "type": "quote",
            "quote": {
                "rich_text": [{"type": "text", "text": {"content": content}}]
            }
        }
    
    def code(self, content: str, language: str = "plain text") -> Dict:
        return {
            "object": "block",
            "type": "code",
            "code": {
                "rich_text": [{"type": "text", "text": {"content": content}}],
                "language": language
            }
        }
    
    def divider(self) -> Dict:
        return {
            "object": "block",
            "type": "divider",
            "divider": {}
        }
    
    def toggle(self, content: str) -> Dict:
        return {
            "object": "block",
            "type": "toggle",
            "toggle": {
                "rich_text": [{"type": "text", "text": {"content": content}}]
            }
        }
    
    def callout(self, content: str, icon: str = "💡") -> Dict:
        return {
            "object": "block",
            "type": "callout",
            "callout": {
                "rich_text": [{"type": "text", "text": {"content": content}}],
                "icon": {
                    "type": "emoji",
                    "emoji": icon
                }
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
    
    
class MarkdownParser:
    """
    A parser class for converting markdown content to Notion-compatible blocks.
    
    This class handles parsing markdown syntax and converting it to the appropriate
    Notion block types using the NotionChildrenWriter.
    """
    
    def __init__(self):
        """Initialize the MarkdownParser."""
        self.writer = NotionChildrenWriter()
    
    def parse_inline_formatting(self, text: str) -> List[Dict]:
        """
        Parse inline formatting like bold, italic, code, and links.
        
        Args:
            text (str): The text to parse for inline formatting
            
        Returns:
            List[Dict]: List of rich text objects with formatting
        """
        rich_text = []
        i = 0
        
        while i < len(text):
            # Handle bold (**text**)
            if text[i:i+2] == '**' and '**' in text[i+2:]:
                end = text.find('**', i+2)
                if end != -1:
                    rich_text.append({
                        "type": "text",
                        "text": {"content": text[i+2:end]},
                        "annotations": {"bold": True}
                    })
                    i = end + 2
                    continue
            
            # Handle italic (*text*)
            elif text[i] == '*' and '*' in text[i+1:]:
                end = text.find('*', i+1)
                if end != -1:
                    rich_text.append({
                        "type": "text",
                        "text": {"content": text[i+1:end]},
                        "annotations": {"italic": True}
                    })
                    i = end + 1
                    continue
            
            # Handle inline code (`code`)
            elif text[i] == '`' and '`' in text[i+1:]:
                end = text.find('`', i+1)
                if end != -1:
                    rich_text.append({
                        "type": "text",
                        "text": {"content": text[i+1:end]},
                        "annotations": {"code": True}
                    })
                    i = end + 1
                    continue
            
            # Handle links [text](url)
            elif text[i] == '[' and '](' in text[i:]:
                bracket_end = text.find(']', i)
                if bracket_end != -1:
                    paren_start = text.find('(', bracket_end)
                    if paren_start != -1 and paren_start == bracket_end + 1:
                        paren_end = text.find(')', paren_start)
                        if paren_end != -1:
                            link_text = text[i+1:bracket_end]
                            link_url = text[paren_start+1:paren_end]
                            rich_text.append({
                                "type": "text",
                                "text": {"content": link_text},
                                "href": link_url
                            })
                            i = paren_end + 1
                            continue
            
            # Regular text
            else:
                # Find the next special character
                next_special = len(text)
                for special in ['**', '*', '`', '[']:
                    pos = text.find(special, i)
                    if pos != -1 and pos < next_special:
                        next_special = pos
                
                if next_special < len(text):
                    content = text[i:next_special]
                    i = next_special
                else:
                    content = text[i:]
                    i = len(text)
                
                if content.strip():
                    rich_text.append({
                        "type": "text",
                        "text": {"content": content}
                    })
        
        return rich_text
    
    def create_rich_text_block(self, content: str, block_type: str) -> Dict:
        """
        Create a block with rich text formatting.
        
        Args:
            content (str): The content to format
            block_type (str): The type of block (paragraph, heading_1, etc.)
            
        Returns:
            Dict: Notion block with rich text formatting
        """
        rich_text = self.parse_inline_formatting(content)
        
        if block_type == "paragraph":
            return {
                "object": "block",
                "type": "paragraph",
                "paragraph": {"rich_text": rich_text}
            }
        elif block_type == "heading_1":
            return {
                "object": "block",
                "type": "heading_1",
                "heading_1": {"rich_text": rich_text}
            }
        elif block_type == "heading_2":
            return {
                "object": "block",
                "type": "heading_2",
                "heading_2": {"rich_text": rich_text}
            }
        elif block_type == "heading_3":
            return {
                "object": "block",
                "type": "heading_3",
                "heading_3": {"rich_text": rich_text}
            }
        elif block_type == "bulleted_list_item":
            return {
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {"rich_text": rich_text}
            }
        elif block_type == "numbered_list_item":
            return {
                "object": "block",
                "type": "numbered_list_item",
                "numbered_list_item": {"rich_text": rich_text}
            }
        elif block_type == "quote":
            return {
                "object": "block",
                "type": "quote",
                "quote": {"rich_text": rich_text}
            }
        elif block_type == "toggle":
            return {
                "object": "block",
                "type": "toggle",
                "toggle": {"rich_text": rich_text}
            }
        elif block_type == "callout":
            return {
                "object": "block",
                "type": "callout",
                "callout": {
                    "rich_text": rich_text,
                    "icon": {"type": "emoji", "emoji": "💡"}
                }
            }
        
        # Fallback to paragraph
        return {
            "object": "block",
            "type": "paragraph",
            "paragraph": {"rich_text": rich_text}
        }


def convert_markdown_to_notion_blocks(markdown_content: str) -> List[Dict]:
    """
    Convert markdown content to Notion-compatible blocks.
    
    This function parses markdown content and converts it to a list of
    Notion block objects that can be used with the Notion API.
    
    Args:
        markdown_content (str): The markdown content to convert
        
    Returns:
        List[Dict]: List of Notion-compatible block objects
        
    Example:
        >>> markdown = "# Title\\n\\nThis is **bold** text."
        >>> blocks = convert_markdown_to_notion_blocks(markdown)
        >>> notion.push.create_page_with_blocks(blocks, database_id)
    """
    if not markdown_content or not markdown_content.strip():
        return []
    
    parser = MarkdownParser()
    blocks = []
    lines = markdown_content.split('\n')
    i = 0
    
    # Track list state
    in_bullet_list = False
    in_numbered_list = False
    in_code_block = False
    code_block_content = []
    code_language = "plain text"
    
    while i < len(lines):
        line = lines[i].rstrip()
        
        # Handle code blocks
        if line.startswith('```'):
            if not in_code_block:
                # Start of code block
                in_code_block = True
                code_block_content = []
                # Try to extract language
                if len(line) > 3:
                    code_language = line[3:].strip()
                i += 1
                continue
            else:
                # End of code block
                in_code_block = False
                code_content = '\n'.join(code_block_content)
                blocks.append(parser.writer.code(code_content, code_language))
                i += 1
                continue
        
        if in_code_block:
            code_block_content.append(line)
            i += 1
            continue
        
        # Handle horizontal rules
        if line.strip() in ['---', '***', '___']:
            blocks.append(parser.writer.divider())
            i += 1
            continue
        
        # Handle headers
        if line.startswith('#'):
            level = 0
            while level < len(line) and line[level] == '#':
                level += 1
            
            content = line[level:].strip()
            if content:
                if level == 1:
                    blocks.append(parser.create_rich_text_block(content, "heading_1"))
                elif level == 2:
                    blocks.append(parser.create_rich_text_block(content, "heading_2"))
                elif level >= 3:
                    blocks.append(parser.create_rich_text_block(content, "heading_3"))
            i += 1
            continue
        
        # Handle blockquotes
        if line.startswith('> '):
            content = line[2:].strip()
            if content:
                blocks.append(parser.create_rich_text_block(content, "quote"))
            i += 1
            continue
        
        # Handle bullet lists
        if line.startswith('- ') or line.startswith('* '):
            content = line[2:].strip()
            if content:
                blocks.append(parser.create_rich_text_block(content, "bulleted_list_item"))
                in_bullet_list = True
            i += 1
            continue
        
        # Handle numbered lists
        numbered_match = re.match(r'^\d+\.\s+(.+)$', line)
        if numbered_match:
            content = numbered_match.group(1).strip()
            if content:
                blocks.append(parser.create_rich_text_block(content, "numbered_list_item"))
                in_numbered_list = True
            i += 1
            continue
        
        # Handle task lists
        task_match = re.match(r'^-\s+\[([ x])\]\s+(.+)$', line)
        if task_match:
            checked = task_match.group(1) == 'x'
            content = task_match.group(2).strip()
            if content:
                # Create a toggle block for task items
                blocks.append(parser.create_rich_text_block(content, "toggle"))
            i += 1
            continue
        
        # Handle empty lines
        if not line.strip():
            # End lists on empty lines
            if in_bullet_list or in_numbered_list:
                in_bullet_list = False
                in_numbered_list = False
            i += 1
            continue
        
        # Handle regular paragraphs
        if line.strip():
            blocks.append(parser.create_rich_text_block(line, "paragraph"))
        
        i += 1
    
    return blocks


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

    def create_page_with_blocks(self, properties: Dict, blocks: List[Dict], database_id: str) -> Dict:
        """
        Create a new Notion page with content blocks.
        
        Args:
            properties (Dict): Page properties
            blocks (List[Dict]): List of Notion block objects
            database_id (str): ID of the parent database
            
        Returns:
            Dict: Response from Notion API
        """
        body = {
            'parent': {'database_id': database_id},
            'properties': properties,
            'children': blocks
        }
        response = requests.post(
            self.base_url + '/pages',
            headers=self.headers,
            json=body
        )
        return response.json()

    def append_blocks(self, page_id: str, blocks: List[Dict]) -> Dict:
        """
        Append blocks to an existing Notion page.
        
        Args:
            page_id (str): ID of the page to append blocks to
            blocks (List[Dict]): List of Notion block objects
            
        Returns:
            Dict: Response from Notion API
        """
        url = f"{self.base_url}/blocks/{page_id}/children"
        body = {'children': blocks}
        response = requests.patch(url, headers=self.headers, json=body)
        return response.json()

    def update_page_with_blocks(self, page_id: str, properties: Dict, blocks: List[Dict]) -> Dict:
        """
        Update an existing Notion page with new properties and blocks.
        
        Args:
            page_id (str): ID of the page to update
            properties (Dict): New page properties
            blocks (List[Dict]): List of Notion block objects
            
        Returns:
            Dict: Response from Notion API
        """
        # First update the page properties
        self.update_page(page_id, properties)
        
        # Then replace all blocks
        url = f"{self.base_url}/blocks/{page_id}/children"
        body = {'children': blocks}
        response = requests.patch(url, headers=self.headers, json=body)
        return response.json()


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
            try:
                response.get('results')
                all_results.extend(response['results'])
                has_more = response.get('has_more', False)
                next_cursor = response.get('next_cursor')
                return {'results': all_results}

            except:
                return response.json()

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

    def create_page_from_markdown(self, markdown_content: str, properties: Dict, database_id: str) -> Dict:
        """
        Create a new Notion page from markdown content.
        
        Args:
            markdown_content (str): Markdown content to convert
            properties (Dict): Page properties (title, etc.)
            database_id (str): ID of the parent database
            
        Returns:
            Dict: Response from Notion API
            
        Example:
            >>> notion = Notion()
            >>> markdown = "# My Document\\n\\nThis is **bold** text."
            >>> properties = {"Name": notion.writer.title("My Document")}
            >>> result = notion.create_page_from_markdown(markdown, properties, "db-id")
        """
        blocks = convert_markdown_to_notion_blocks(markdown_content)
        return self.push.create_page_with_blocks(properties, blocks, database_id)

    def update_page_from_markdown(self, page_id: str, markdown_content: str, properties: Dict) -> Dict:
        """
        Update an existing Notion page with markdown content.
        
        Args:
            page_id (str): ID of the page to update
            markdown_content (str): Markdown content to convert
            properties (Dict): New page properties
            
        Returns:
            Dict: Response from Notion API
        """
        blocks = convert_markdown_to_notion_blocks(markdown_content)
        return self.push.update_page_with_blocks(page_id, properties, blocks)

    def append_markdown_to_page(self, page_id: str, markdown_content: str) -> Dict:
        """
        Append markdown content to an existing Notion page.
        
        Args:
            page_id (str): ID of the page to append to
            markdown_content (str): Markdown content to convert and append
            
        Returns:
            Dict: Response from Notion API
        """
        blocks = convert_markdown_to_notion_blocks(markdown_content)
        return self.push.append_blocks(page_id, blocks)

# Export main classes
__all__ = ['Notion', 'NotionReader', 'NotionWriter', 'NotionPusher', 'NotionPuller', 'NotionChildrenWriter', 'MarkdownParser', 'convert_markdown_to_notion_blocks'] 
