"""
Cloud Function: push_notion

This function is triggered via HTTP (commonly from Cloud Tasks) and is responsible for pushing structured data to a Notion workspace using the PushNotion client.

The function accepts JSON payloads with the following structure:
{
    "body": dict or str,  # Required: Content to push to Notion
    "page_id": str,       # Optional: Notion page ID to update
    "dummy": bool,        # Optional: Whether this is a dummy operation
    "collection": str     # Optional: Firestore collection to store response
}

If `page_id` is provided, it updates a specific Notion page.
If not, it creates a new entry or performs a default action (as defined by PushNotion).

Structured logs are emitted using CloudLogger and will be available in Google Cloud Logging.
"""

import json
from flask import jsonify, make_response
from packages.Logging import CloudLogger
from packages.Notion import Notion
from packages.Tasks import Tasks, TaskStatus

# ——— Cold-start initialization: do this once per container ————————————————
logger = CloudLogger(logger_name='Push_Notion', prefix = 'Push_Notion')  # Structured GCP logger
push = Notion().push  # Notion client wrapper

# ——— Main HTTP Cloud Function entry point ————————————————————————————————
def push_notion(request):
    """
    Handles HTTP requests to push data into Notion.

    Args:
        request (flask.Request): The HTTP request object containing the JSON payload.

    Expected JSON payload:
        {
            "body": <dict or str>,   # Required: Content to push to Notion
            "page_id": <str>,        # Optional: Notion page ID to update
            "dummy": <bool>,         # Optional: Whether this is a dummy operation
            "collection": <str>      # Optional: Firestore collection to store response
        }

    Returns:
        Flask response object with:
            - 200: Success with Notion response JSON
            - 400: Bad request (invalid JSON or missing body)
            - 500: Internal error (Notion API failure)

    The response includes:
        - Success (200): The JSON response from Notion
        - Error (400/500): Error message as text
    """
    # 1) Parse JSON body from request
    data = request.get_json(silent=True)
    if not data:
        logger.error("No JSON payload")
        return make_response("Invalid JSON", 400)

    # 2) Extract parameters
    body = data.get('body', None)
    page_id = data.get('page_id', None)
    task_name = data.get('task_name', None)

    tasks = Tasks()
    tasks.update_task_status(task_name, TaskStatus.RUNNING)

    if body is None:
        logger.error("Missing 'body' in payload")
        return make_response("Missing 'body' field", 400)

    # 3) Push to Notion via helper class
    try:
        if page_id:
            # Update specific Notion page
            resp = push.push_to_notion(body, page_id)
        else:
            # Create new page or perform default action
            resp = push.push_to_notion(body)

    except Exception as e:
        logger.error(f"Exception pushing to Notion: {e}")
        tasks.update_task_status(task_name, TaskStatus.FAILED, str(e))
        return make_response(str(e), 500)

    # 4) Return response to caller
    if resp.status_code == 200:
        logger.info("Notion update succeeded.")
        tasks.update_task_status(task_name, TaskStatus.COMPLETED)
        return jsonify(resp.json()), 200
    else:
        logger.error(f"Notion update failed: {resp.status_code} {resp.text}")
        return make_response(resp.text, resp.status_code)