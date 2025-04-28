import requests
from flask import Request, jsonify
from packages.Logging import CloudLogger
from packages.WriteNotion import WriteNotion
from packages.Tasks import Tasks, TaskConfig

logger = CloudLogger("purple_gold")

def publish_discord(payload: dict):
    """
    Forwards message to push_message endpoint for Discord publishing.
    """
    try:
        response = requests.post(
            "https://europe-west1-digital-africa-rainbow.cloudfunctions.net/push_message",
            json={"message": payload}
        )
        response.raise_for_status()
        logger.info(f"[publish_discord] Message sent to Discord: {response.status_code}")
    except requests.RequestException as e:
        logger.error(f"[publish_discord] Failed to send message to Discord: {e}")

# Shared push function to Notion
def push_to_notion(properties: dict, icon: dict):
    body = {
        "parent": {"database_id": "1db0fcf384948062a5a5c3732981feb3"},
        "properties": properties, 
        "icon": icon
    }

    url = "https://europe-west1-digital-africa-rainbow.cloudfunctions.net/push_notion"

    try:
        response = requests.post(url, json={"body": body})
        response.raise_for_status()
        logger.info(f"[push_to_notion] Notion push successful: {response.status_code}")
    except requests.RequestException as e:
        logger.error(f"[push_to_notion] Failed to push to Notion: {e}")
        raise

def enqueue_push_to_notion(properties: dict, icon: dict):
    """
    Enqueues a task to push data to Notion asynchronously using the notion-queue.
    """
    tasks_client = Tasks()
    
    body = {
        "parent": {"database_id": "1db0fcf384948062a5a5c3732981feb3"},
        "properties": properties,
        "icon": icon
    }
    
    task_params = {
        "url": "https://europe-west1-digital-africa-rainbow.cloudfunctions.net/push_notion",
        "payload": {"body": body},
        "queue": "notion-queue"  # Specify the notion-queue
    }
    
    task_name = tasks_client.add_task(task_params)
    if task_name:
        logger.info(f"[enqueue_push_to_notion] Task enqueued successfully in notion-queue: {task_name}")
    else:
        logger.error("[enqueue_push_to_notion] Failed to enqueue task in notion-queue")
        raise RuntimeError("Failed to enqueue Notion push task")

def golden_above_purple(data: dict):
    publish_discord(data)
    writer = WriteNotion()
    properties = {
        "Alert Name": writer.title(data.get("title", "unknown")),
        "trigger": writer.select(data.get("title", "unknown")),
        "sentiment": writer.select("Bearish"),
        "interval": writer.select(str(data.get("interval", "unknown"))),
        "ticker": writer.select(data.get("ticker", "unknown")),
        "close": writer.number(data.get("close", 0)),
        "volume": writer.number(data.get("volume", 0)),
        "description": writer.text(data.get("message", ""))
    }
    icon = {'type': 'external',
            'external': {'url': 'https://www.notion.so/icons/arrow-down-line_yellow.svg'}}
    enqueue_push_to_notion(properties, icon)

def purple_above_golden(data: dict):
    publish_discord(data)
    writer = WriteNotion()
    properties = {
        "Alert Name": writer.title(data.get("title", "unknown")),
        "trigger": writer.select(data.get("title", "unknown")),
        "sentiment": writer.select("Bullish"),
        "interval": writer.select(str(data.get("interval", "unknown"))),
        "ticker": writer.select(data.get("ticker", "unknown")),
        "close": writer.number(data.get("close", 0)),
        "volume": writer.number(data.get("volume", 0)),
        "description": writer.text(data.get("message", ""))
    }
    icon = {'type': 'external',
            'external': {'url': 'https://www.notion.so/icons/arrow-down-line_purple.svg'}}
    enqueue_push_to_notion(properties, icon)

def limit(data: dict):
    publish_discord(data)
    writer = WriteNotion()
    properties = {
        "Alert Name": writer.title("limit"),
        "trigger": writer.select("limit"),
        "ticker": writer.select(data.get("ticker", "unknown")),
        "close": writer.number(data.get("close", 0)),
        "description": writer.text(data.get("message", ""))
    }
    icon = {'type': 'external',
        'external': {'url': 'https://www.notion.so/icons/command-line_gray.svg'}}
    enqueue_push_to_notion(properties, icon)


def purple_gold(request: Request):
    """
    Entry point Cloud Function triggered via HTTP.
    Expects JSON payload from TradingView with fields like:
    {
        "title": "golden_above_purple",
        "interval": "15",
        "ticker": "BTCUSD",
        "close": 64500,
        "volume": 1200,
        "message": "optional message to Discord"
    }
    """
    logger.debug("[purple_gold] Received request")
    try:
        payload = request.get_json(force=True)
        logger.debug(f"[purple_gold] Payload: {payload}")
    except Exception as e:
        logger.error(f"[purple_gold] Invalid JSON: {e}")
        return jsonify({"error": "Invalid JSON"}), 400

    # Dispatch to Notion handler
    alert_type = payload.get("alert_type")
    if not alert_type:
        logger.warning("[purple_gold] Missing 'alert_type' in payload")
        return jsonify({"error": "Missing 'alert_type' field"}), 400
    
    logger.debug(f"[purple_gold] Payload: {alert_type}")
    HANDLERS = {
        "purple_above_golden": purple_above_golden,
        "golden_above_purple": golden_above_purple,
        "limit": limit
    }

    handler = HANDLERS.get(alert_type)
    if not handler:
        logger.warning(f"[purple_gold] Unknown alert type: {alert_type}")
        return jsonify({"error": f"Unknown alert type '{alert_type}'"}), 400

    try:
        handler(payload)
        return jsonify({"status": "ok", "handled_by": alert_type}), 200
    except Exception as e:
        logger.error(f"[purple_gold] Handler error: {e}")
        return jsonify({"error": str(e)}), 500