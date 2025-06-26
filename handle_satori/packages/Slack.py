"""
A Slack integration module for sending messages via webhooks and the Slack API.

This module provides functionality to:
1. Send messages to Slack channels using webhooks
2. Send messages using the Slack API
3. Build formatted messages with user/group mentions
4. Send direct messages to users

Example:
    >>> # Send a webhook message
    >>> send_slack_webhook("https://hooks.slack.com/webhook", "Hello World!")
    >>> 
    >>> # Send an API message
    >>> send_slack_api_message("#general", "Hello World!", "slack-token")
    >>> 
    >>> # Send a direct message
    >>> send_direct_message("U123", "Hello there!")
    >>> 
    >>> # Build a message with mentions
    >>> builder = SlackMessageBuilder()
    >>> message = builder.text("Hello").ping_user("U123").build()
"""

import requests
from google.cloud import secretmanager
import logging
from typing import Dict, List, Optional, Any
import os
import json
import packages.Notion as Notion
from packages.SecretAccessor import SecretAccessor

# Configure logging
logger = logging.getLogger(__name__)

class SlackConfig:
    """Configuration constants for Slack integration"""
    
    EMOJI = {
        "info": ":information_source:",
        "success": ":white_check_mark:",
        "warning": ":warning:",
        "error": ":x:",
        "rocket": ":rocket:",
        "wave": ":wave:",
    }
    
    CHANNEL = {
        "general": "CV91D4HL4",
        "fuze": "C03J6AXJR8X",
        "platform": "C06DG8FCSBB",
        "pipeline": "C074D6MCRSB",
        "feedback_notion": "C08J57BQZFX",
    }
    
    NOTION_TEAM_DB_ID = '550eb00f314f4f20a3ffd2cb9f5504de'
    BASE_API_URL = "https://slack.com/api"
    
    @staticmethod
    def get_bot_token() -> str:
        """Get Slack bot token from environment"""
        return os.getenv('SLACK_BOT_TOKEN', '')

class SlackAPI:
    """Handles all Slack API interactions"""
    
    def __init__(self, token: Optional[str] = None):
        self.token = SecretAccessor().get_secret("SLACK_Puppy")
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
    
    def get_usergroups(self) -> Dict[str, str]:
        """Fetch usergroups from Slack API"""
        response = requests.get(
            f"{SlackConfig.BASE_API_URL}/usergroups.list",
            headers=self.headers
        )
        data = response.json()
        if not data.get("ok"):
            logger.error(f"Failed to fetch usergroups: {data.get('error')}")
            return {}
        return {
            element['name']: element['id'] 
            for element in data.get("usergroups", [])
        }
    
    def send_message(self, channel: str, text: str) -> bool:
        """Send message via Slack API"""
        # Get channel ID from channel name if it exists in the lookup dictionary
        channel_id = SlackConfig.CHANNEL.get(channel, channel)
        
        response = requests.post(
            f"{SlackConfig.BASE_API_URL}/chat.postMessage",
            headers=self.headers,
            json={"channel": channel_id, "text": text}
        )
        data = response.json()
        if not data.get("ok"):
            logger.error(f"Failed to send message: {data.get('error')}")
            return False
        return True

    def send_direct_message(self, user_id: str, text: str) -> bool:
        """Send a direct message to a user via Slack API
        
        Args:
            user_id: Slack user ID (e.g., "U12345678")
            text: Message text to send
            
        Returns:
            bool: True if message was sent successfully, False otherwise
        """
        # First, open a direct message conversation
        response = requests.post(
            f"{SlackConfig.BASE_API_URL}/conversations.open",
            headers=self.headers,
            json={"users": user_id}
        )
        data = response.json()
        
        if not data.get("ok"):
            logger.error(f"Failed to open conversation: {data.get('error')}")
            return False
            
        # Get the channel ID from the response
        channel_id = data.get("channel", {}).get("id")
        if not channel_id:
            logger.error("No channel ID returned from conversation.open")
            return False
            
        # Send the message to the direct message channel
        return self.send_message(channel_id, text)

class SlackCache:
    """Manages caching of Slack data"""
    
    def __init__(self):
        self._people: Optional[List[Dict[str, Any]]] = None
        self._groups: Optional[Dict[str, str]] = None
        self._api = SlackAPI()
        self._notion = Notion.Notion()
    
    def _get_people_(self) -> List[Dict[str, Any]]:
        """Get cached people data"""
        if self._people is None:
            P = self._notion.pull.query_database(
                SlackConfig.NOTION_TEAM_DB_ID, 
                {'property': 'Left the team', 'checkbox': {'equals': False}}
            )
            self._people = [
                {
                    'Slack ID': self._notion.reader.text(person['properties']['Slack ID']),
                    'Person': person['properties']['Person']['people'][0]['name'],
                    'Notion ID': self._notion.reader.text(person['properties']['Notion ID']),
                    'Affinity ID': self._notion.reader.number(person['properties']['Affinity ID'])
                }
                for person in P['results']
            ]
        return self._people
    
    def get_people(self) -> List[Dict[str, Any]]:
        """Get cached people data"""
        if self._people is None:
            with open('people.json', 'r') as f:
                self._people = json.loads(f.read())
        return self._people

    def _get_groups_(self) -> Dict[str, str]:
        """Get cached groups data"""
        if self._groups is None:
            self._groups = self._api.get_usergroups()
        return self._groups

    def get_groups(self) -> Dict[str, str]:
        """Get cached groups data"""
        if self._groups is None:
            with open('groups.json', 'r') as f:
                self._groups = json.loads(f.read())
        return self._groups

class SlackMessageBuilder:
    """Builds formatted Slack messages with mentions"""
    
    def __init__(self):
        self._message = ""
        self._cache = SlackCache()
    
    def text(self, content: str) -> 'SlackMessageBuilder':
        """Add text content to the message"""
        self._message += content
        return self
    
    def emoji(self, name: str) -> 'SlackMessageBuilder':
        """Add an emoji to the message"""
        if emoji := SlackConfig.EMOJI.get(name):
            self._message += f" {emoji}"
        return self
    
    def url(self, url: str, text: Optional[str] = None) -> 'SlackMessageBuilder':
        """Add a URL to the message with optional custom text
        
        Args:
            url: The URL to link to
            text: Optional custom text to display (defaults to the URL if not provided)
            
        Example:
            >>> builder = SlackMessageBuilder()
            >>> builder.url("https://example.com", "Click here")
            >>> # Result: <https://example.com|Click here>
        """
        if text:
            self._message += f" <{url}|{text}>"
        else:
            self._message += f" <{url}>"
        return self
    
    def ping_user(self, identifier: str) -> 'SlackMessageBuilder':
        """Add a user mention using any identifier"""
        search_value = str(identifier).lower()
        for person in self._cache.get_people():
            if any(str(value).lower() == search_value for value in person.values()):
                self._message += f" <@{person['Slack ID']}>"
                return self
        logger.warning(f"User not found: {identifier}")
        return self
    
    def ping_group(self, identifier: str) -> 'SlackMessageBuilder':
        """Add a group mention using name or ID"""
        search_value = str(identifier).lower()
        groups = self._cache.get_groups()
        
        # Try direct or case-insensitive match
        for name, group_id in groups.items():
            if name.lower() == search_value or group_id.lower() == search_value:
                self._message += f" <!subteam^{group_id}>"
                return self
        
        logger.warning(f"Group not found: {identifier}")
        return self
    
    def build(self) -> str:
        """Build the final message"""
        return self._message.strip()

def send_message(channel: str, message: str) -> bool:
    """Convenience function to send a message via Slack API"""
    return SlackAPI().send_message(channel, message)

def send_webhook(webhook_url: str, message: str) -> bool:
    """Send a message via webhook"""
    try:
        response = requests.post(
            webhook_url, 
            json={"text": message},
            timeout=5
        )
        if response.status_code != 200:
            logger.error(f"Webhook failed: {response.status_code} - {response.text}")
            return False
        return True
    except requests.RequestException as e:
        logger.error(f"Webhook error: {str(e)}")
        return False

def send_slack_webhook(webhook_url: str, message: str):
    """
    Send a message to Slack using a webhook URL.
    
    Args:
        webhook_url: The Slack webhook URL to send the message to.
        message: The text message to send.
        
    Example:
        >>> send_slack_webhook(
        ...     "https://hooks.slack.com/services/xxx/yyy/zzz",
        ...     "Hello from Python!"
        ... )
    """
    payload = {"text": message}
    try:
        response = requests.post(webhook_url, json=payload, timeout=5)
        if response.status_code != 200:
            logger.error(f"Slack webhook failed: {response.status_code} - {response.text}")
        else:
            logger.info(f"Slack webhook sent successfully")
    except requests.RequestException as e:
        logger.error(f"Error sending Slack webhook: {str(e)}")

def send_slack_api_message(channel: str, message: str, secret_id: str):
    """
    Send a message to a Slack channel using the Slack API.
    
    Args:
        channel: The Slack channel to send the message to (e.g., "#general" or "@username").
        message: The text message to send.
        secret_id: The ID of the secret containing the Slack API token.
        
    Example:
        >>> send_slack_api_message(
        ...     "#general",
        ...     "Hello from Python!",
        ...     "slack-bot-token"
        ... )
    """
    token = SecretAccessor().get_secret("SLACK_Puppy")
    url = "https://slack.com/api/chat.postMessage"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    payload = {"channel": channel, "text": message}

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=5)
        resp_data = response.json()
        if not resp_data.get("ok"):
            logger.error(f"Slack API error: {resp_data.get('error')}")
        else:
            logger.info(f"Slack API message sent to channel {channel}")
    except requests.RequestException as e:
        logger.error(f"Error sending Slack API message: {str(e)}")

def get_people():
    notion = Notion.Notion()
    P = notion.pull.query_database('550eb00f314f4f20a3ffd2cb9f5504de', {'property': 'Left the team', 'checkbox': {'equals': False}})
    P = [e['properties'] for e in P['results']]
    people = [
        {
            'Slack ID': notion.reader.text(person['Slack ID']), 
            'Person': person['Person']['people'][0]['name'],
            'Notion ID': notion.reader.text(person['Notion ID']),
            'Affinity ID': notion.reader.number(person['Affinity ID'])
        } 
        for person in P]
    return people

def get_groups():
    
    SLACK_BOT_TOKEN = SecretAccessor().get_secret("SLACK_Puppy")

    response = requests.get(
        "https://slack.com/api/usergroups.list",
        headers={"Authorization": f"Bearer {SLACK_BOT_TOKEN}"}
    )

    data = response.json()
    group = {}
    for element in data["usergroups"]:
        group[element['name']] = element['id']
    return group

def send_direct_message(user_id: str, message: str) -> bool:
    """Convenience function to send a direct message to a user
    
    Args:
        user_id: Slack user ID (e.g., "U12345678") or any identifier that can be resolved to a user
        message: Message text to send
        
    Returns:
        bool: True if message was sent successfully, False otherwise
        
    Example:
        >>> send_direct_message("U12345678", "Hello there!")
        >>> send_direct_message("john.doe", "Hello there!")  # Will look up user by name
    """
    # If the user_id is not a Slack ID, try to resolve it
    if not user_id.startswith("U"):
        cache = SlackCache()
        for person in cache.get_people():
            if any(str(value).lower() == user_id.lower() for value in person.values()):
                user_id = person['Slack ID']
                break
        else:
            logger.error(f"Could not resolve user: {user_id}")
            return False
            
    return SlackAPI().send_direct_message(user_id, message)

def get_slack_person_id(email):
    # Your OAuth token
    oauth_token = SecretAccessor().get_secret("SLACK_Puppy")
    # Email address of the user you want to look up
    # Set the API endpoint
    url = 'https://slack.com/api/users.lookupByEmail'
    # Set the headers
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Authorization': f'Bearer {oauth_token}'
    }
    # Set the payload
    payload = {
                'email': email
            }
    # Make the request
    response = requests.get(url, headers=headers, params=payload)
    # Parse the response
    data = response.json()
    if data['ok']:
        slack_id = data['user']['id']
        return slack_id
# ------------------ EXPORT ------------------

__all__ = [
    "send_slack_webhook",
    "send_slack_api_message",
    "send_direct_message",
    "SlackMessageBuilder",
]
