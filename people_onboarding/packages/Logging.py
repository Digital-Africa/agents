from google.cloud import logging as cloud_logging
import logging  # Import standard Python logging module
import json


class CloudLogger(object):
    def __init__(self, logger_name):
        # Set up Google Cloud Logging with credentials
        self.service_account = 'sa_keys/puppy-logging-key.json'
        self.cloud_logging_client = cloud_logging.Client.from_service_account_json(self.service_account)
        self.cloud_logging_client.setup_logging()

        # Set up Python logger
        self.logger = logging.getLogger(logger_name)
        self.logger.setLevel(logging.DEBUG)

    def _format_message(self, msg, extra=None):
        """Format the log message with extra parameters if provided."""
        if extra:
            # Convert extra dict to JSON string and append to message
            extra_str = json.dumps(extra)
            return f"{msg} | Extra: {extra_str}"
        return msg

    def info(self, msg, extra=None):
        formatted_msg = self._format_message(msg, extra)
        self.logger.info(formatted_msg)

    def warning(self, msg, extra=None):
        formatted_msg = self._format_message(msg, extra)
        self.logger.warning(formatted_msg)

    def error(self, msg, extra=None):
        formatted_msg = self._format_message(msg, extra)
        self.logger.error(formatted_msg)

    def debug(self, msg, extra=None):
        formatted_msg = self._format_message(msg, extra)
        self.logger.debug(formatted_msg)
