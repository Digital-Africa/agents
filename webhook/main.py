"""
Cloud Function: webhook

This function acts as a routing layer that receives an HTTP JSON payload specifying a `target`.
It dispatches the payload to the corresponding handler function, allowing for custom actions.

The function supports different types of webhook payloads:
{
    "target": "trading_view",  # or "beta"
    "data": { ... }  # Payload data to be processed
}

Structured logs are emitted using CloudLogger.
"""

from flask import Request, jsonify
from packages.Logging import CloudLogger
from packages.Action import process_simple_direct_message

# Initialize structured Cloud Logging
logger = CloudLogger("webhook")

# Mapping of target names to handler functions
HANDLERS = {
    "direct_message": process_simple_direct_message,
}

# ——— Cloud Function Entry Point —————————————————————————————————————————
def webhook(request: Request):
    """
    Cloud Function HTTP entry point.

    Accepts JSON payload with the following structure:
    {
        "target": "trading_view" | "beta",  # Specifies which handler to use
        "data": { ... }  # Payload data to be processed by the handler
    }

    Returns:
        - 200: Success with handler result
        - 400: Bad request (malformed payload or unknown target)
        - 500: Internal server error (handler execution failed)

    The response includes:
        - status: "ok" on success
        - target: The target that was processed
        - result: The output from the handler function
    """
    logger.debug("[webhook] Incoming request received")
    try:
        payload = request.get_json(force=True)
        custom_header = request.headers.get("X-database")
        logger.debug(f"[webhook] Parsed JSON: {payload}")
        logger.debug(f"[webhook] header catched JSON: {custom_header}")
    except Exception as e:
        logger.error(f"[webhook] Failed to parse JSON: {e}")
        return "Invalid JSON", 400

    target = payload.get("target", "direct_message")
    if not target:
        logger.warning(f"[webhook] Missing 'target' in payload: {payload}")
        return "Missing 'target' field", 400

    handler = HANDLERS.get(target)
    if handler is None:
        logger.warning(f"[webhook] Unknown target: {target}")
        return f"Unknown target '{target}'", 400

    try:
        logger.info(f"[webhook] Dispatching to handler '{target}'")
        result = handler(payload)

    except Exception as e:
        logger.error(f"[webhook] Handler error for target '{target}': {e}")
        return jsonify({"error": str(e)}), 500

    logger.info(f"[webhook] Successfully processed target '{target}'")
    return jsonify({
        "status": "ok",
        "target": target,
        "result": result,
    }), 200