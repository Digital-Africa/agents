import requests
import logging
from typing import Dict, Optional, Union
from datetime import datetime
import json
from dataclasses import dataclass
from enum import Enum

class LogLevel(Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

@dataclass
class DiscordMessage:
    content: str
    username: Optional[str] = None
    avatar_url: Optional[str] = None
    tts: bool = False
    embeds: Optional[list] = None

class WebhookException(Exception):
    """Base exception for webhook-related errors"""
    pass

class WebhookLogger:
    def __init__(self, log_level: str = "INFO"):
        self.logger = logging.getLogger("DiscordWebhook")
        self.logger.setLevel(log_level)
        
        # Create console handler if no handlers exist
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

    def log_success(self, webhook_name: str, message: str):
        self.logger.info(f"Successfully sent message to webhook '{webhook_name}': {message}")

    def log_error(self, webhook_name: str, error: str):
        self.logger.error(f"Failed to send message to webhook '{webhook_name}': {error}")

    def log_debug(self, message: str):
        self.logger.debug(message)

class DiscordWebhook:
    def __init__(self, webhooks: Dict[str, str], log_level: str = "INFO"):
        """
        Initialize the Discord webhook manager.
        
        Args:
            webhooks: Dictionary mapping webhook names to their URLs
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        self.webhooks = webhooks
        self.logger = WebhookLogger(log_level)
        self.session = requests.Session()

    def send_message(
        self,
        webhook_name: str,
        content: str,
        username: Optional[str] = None,
        avatar_url: Optional[str] = None,
        tts: bool = False,
        embeds: Optional[list] = None
    ) -> bool:
        """
        Send a message to a specified webhook.
        
        Args:
            webhook_name: Name of the webhook to use
            content: Message content
            username: Override default username
            avatar_url: Override default avatar
            tts: Whether to use text-to-speech
            embeds: List of embed objects
            
        Returns:
            bool: True if message was sent successfully, False otherwise
        """
        if webhook_name not in self.webhooks:
            error_msg = f"Webhook '{webhook_name}' not found"
            self.logger.log_error(webhook_name, error_msg)
            raise WebhookException(error_msg)

        webhook_url = self.webhooks[webhook_name]
        message = DiscordMessage(
            content=content,
            username=username,
            avatar_url=avatar_url,
            tts=tts,
            embeds=embeds
        )

        try:
            response = self.session.post(
                webhook_url,
                json=message.__dict__,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            
            self.logger.log_success(webhook_name, content)
            return True
            
        except requests.exceptions.RequestException as e:
            self.logger.log_error(webhook_name, str(e))
            return False

    def create_embed(
        self,
        title: str,
        description: str,
        color: int = 0x00ff00,
        fields: Optional[list] = None,
        footer: Optional[dict] = None,
        timestamp: Optional[datetime] = None
    ) -> dict:
        """
        Create a Discord embed object.
        
        Args:
            title: Embed title
            description: Embed description
            color: Embed color (hex)
            fields: List of field objects
            footer: Footer object
            timestamp: Timestamp for the embed
            
        Returns:
            dict: Discord embed object
        """
        embed = {
            "title": title,
            "description": description,
            "color": color,
        }
        
        if fields:
            embed["fields"] = fields
            
        if footer:
            embed["footer"] = footer
            
        if timestamp:
            embed["timestamp"] = timestamp.isoformat()
            
        return embed

    def create_field(self, name: str, value: str, inline: bool = False) -> dict:
        """
        Create a field for Discord embeds.
        
        Args:
            name: Field name
            value: Field value
            inline: Whether the field should be inline
            
        Returns:
            dict: Field object
        """
        return {
            "name": name,
            "value": value,
            "inline": inline
        }

    def create_footer(self, text: str, icon_url: Optional[str] = None) -> dict:
        """
        Create a footer for Discord embeds.
        
        Args:
            text: Footer text
            icon_url: Footer icon URL
            
        Returns:
            dict: Footer object
        """
        footer = {"text": text}
        if icon_url:
            footer["icon_url"] = icon_url
        return footer
