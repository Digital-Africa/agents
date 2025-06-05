from google.cloud import logging as cloud_logging
import logging  # Import standard Python logging module


class CloudLogger(object):
    def __init__(self, logger_name):
        # Set up Google Cloud Logging with credentials
        self.service_account = 'sa_keys/puppy-logging-key.json'
        self.cloud_logging_client = cloud_logging.Client.from_service_account_json(self.service_account)
        self.cloud_logging_client.setup_logging()

        # Set up Python logger
        self.logger = logging.getLogger(logger_name)
        self.logger.setLevel(logging.DEBUG)

    def info(self, msg):
        self.logger.info(msg)

    def warning(self, msg):
        self.logger.warning(msg)

    def error(self, msg):
        self.logger.error(msg)

    def debug(self, msg):
        self.logger.debug(msg)
