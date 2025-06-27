"""
Cloud Function: push_message

This function receives an HTTP POST request with a JSON payload containing a `"message"` field.
It then sends this message to both Slack and Discord using webhook URLs stored securely in Google Secret Manager.

Modules:
- Flask (Request, jsonify) for handling HTTP requests
- Google Cloud Secret Manager to securely retrieve webhook URLs
- CloudLogger for smart Cloud Logging
"""

import os
import requests
from flask import Request, jsonify
from google.cloud import secretmanager
from google.oauth2 import service_account
from packages.Logging import CloudLogger
from packages.SecretAccessor import SecretAccessor


# Initialize structured Cloud Logging
logger = CloudLogger("push_message")

def post_to_slack(message: str) -> dict:
    """
    Sends a message to Slack via webhook.

    Args:
        message (str): The message content.

    Returns:
        dict: Contains status code, truncated response, and metadata.
    """
    payload = {"text": message}
    logger.info("[post_to_slack] Sending message to Slack")
    try:
        resp = requests.post(SLACK_WEBHOOK_URL, json=payload)
        response = {
            "message_app": "slack",
            "status_code": resp.status_code,
            "response": resp.text[:200],
        }
        logger.info(f"[post_to_slack] Response: {response}")
        return response
    except Exception as e:
        logger.error(f"[post_to_slack] Error: {e}")
        raise

def post_to_discord(data: str) -> dict:
    """
    Sends a message to Discord via webhook.

    Args:
        message (str): The message content.

    Returns:
        dict: Contains status code, original content, truncated response, and metadata.
    """
    content = data.get('message')
    agent = content.get('title')
    payload = {"content": content.get('message')}
    WEBHOOK_URL=HANDLERS.get(agent)
    logger.info(f"[post_to_discord] Sending message to Discord:{agent}")
    try:
        resp = requests.post(WEBHOOK_URL, json=payload)
        response = {
            "message_app": "discord",
            "content": content,
            "status_code": resp.status_code,
            "response": resp.text[:200],
        }
        logger.info(f"[post_to_discord] Response: {response}")
        return response
    except Exception as e:
        logger.error(f"[post_to_discord] Error: {e}")
        raise

# Securely retrieve webhook URLs at cold start
secrets = SecretAccessor()

HANDLERS = {
    "golden_above_purple": secrets.get_token('golden_above_purple'),
    "purple_above_golden": secrets.get_token('purple_above_golden'),
    "limit": secrets.get_token('limit'),
    'DISCORD_WEBHOOK_URL': secrets.get_token("DISCORD_WEBHOOK_URL"),
    'SLACK_WEBHOOK_URL': secrets.get_token("DISCORD_WEBHOOK_URL")
} 
def push_message(request: Request):
    """
    Cloud Function Entry Point.
    Receives a JSON payload and posts a message to Discord (optionally Slack).

    Request JSON:
        {
            "message": "Hello World"
        }

    Returns:
        HTTP 200 with success response or HTTP 400/500 on error.
    """
    logger.debug("[push_message] Received request")
    
    try:
        data = request.get_json(force=True)
        logger.debug(f"[push_message] Parsed payload: {data}")
    except Exception as e:
        logger.error(f"[push_message] Invalid JSON: {e}")
        return jsonify({"error": "Invalid JSON"}), 400

    message = data.get("message")
    if not message:
        logger.warning("[push_message] Missing 'message' field")
        return jsonify({"error": 'Missing field "message"'}), 400

    try:
        # Optionally send to Slack
        # slack_resp = post_to_slack(message)

        # Send to Discord
        response = post_to_discord(data)
    except Exception as e:
        logger.error(f"[push_message] Exception while posting: {e}")
        return jsonify({"error": str(e)}), 500

    if response["status_code"] not in [200, 204]:
        logger.error(f"[push_message] Webhook failed: {response}")
        return jsonify(response), 500

    logger.info("[push_message] Message successfully posted")
    return jsonify(response), 200