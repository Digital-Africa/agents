from google.cloud import secretmanager
from google.oauth2 import service_account
from google.auth import default
from packages.Logging import CloudLogger
import os

class SecretAccessor:
    """
    Utility class to access secrets from Google Secret Manager using Google Application Credentials
    with fallback to service account file for local development.
    """

    def __init__(self, key_path: str = None, project_id: str = "digital-africa-rainbow"):
        self.project_id = project_id
        self.logger = CloudLogger("SecretAccessor").logger
        
        # Try Google Application Credentials first (for cloud deployment)
        try:
            self.creds, _ = default()
            self.client = secretmanager.SecretManagerServiceClient(credentials=self.creds)
            self.logger.info(f"[init] SecretAccessor initialized with Google Application Credentials for project: {project_id}")
            return
        except Exception as e:
            self.logger.warning(f"[init] Failed to use Google Application Credentials: {e}")

    def get_secret(self, token_name: str, version: str = "latest") -> str:
        """
        Fetches a secret from Google Secret Manager.

        Args:
            token_name (str): Name of the secret.
            version (str): Version of the secret (default: "latest").

        Returns:
            str: The secret value.
        """
        try:
            secret_path = f"projects/{self.project_id}/secrets/{token_name}/versions/{version}"
            self.logger.debug(f"[get_token] Fetching secret: {secret_path}")
            response = self.client.access_secret_version(name=secret_path)
            secret_value = response.payload.data.decode("utf-8")
            self.logger.info(f"[get_token] Successfully retrieved secret: {token_name}")
            return secret_value
        except Exception as e:
            self.logger.error(f"[get_token] Error retrieving secret '{token_name}': {e}")
            raise