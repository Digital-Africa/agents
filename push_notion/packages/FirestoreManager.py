"""
Firestore Manager for Push Notion

This module provides functionality to:
1. Store Notion operation responses in Firestore
2. Track operation history
3. Manage collections and documents
"""

from google.cloud import firestore
from google.oauth2 import service_account
from datetime import datetime
from typing import Dict, Any, Optional
from packages.Logging import CloudLogger

class FirestoreManager:
    """Manages Firestore operations for Push Notion."""
    
    def __init__(self):
        """Initialize the Firestore client."""
        self.logger = CloudLogger(logger_name='Firestore_Manager')
        self.default_creds = "sa_keys/puppy-executor-key.json"
        self.credentials = service_account.Credentials.from_service_account_file(self.default_creds)
        self.db = firestore.Client(credentials=self.credentials, project=self.credentials.project_id, database="memory-bank")
    
    def store_notion_response(self, 
                            collection: str,
                            data: Dict,
                            doc_id: Optional[str] = None) -> str:
        """
        Store Notion operation response in Firestore.
        
        Args:
            collection (str): Name of the Firestore collection
            data (Dict): Response data to store
            page_id (Optional[str]): Notion page ID if available
            
        Returns:
            str: Document ID of the created/updated document
        """
        try:
            # Create document data
            doc_data = data
            # Add to collection
            doc_ref = self.db.collection(collection).document(doc_id)
            doc_ref.set(doc_data, merge=True)
            
            self.logger.info(f"Stored response in {collection}/{doc_ref.id}")
            return doc_ref.id
            
        except Exception as e:
            self.logger.error(f"Error storing in Firestore: {e}")
            raise
    
    def get_notion_response(self, collection: str, doc_id: str) -> Optional[Dict]:
        """Retrieve a stored Notion response."""
        try:
            doc_ref = self.db.collection(collection).document(doc_id)
            doc = doc_ref.get()
            return doc.to_dict() if doc.exists else None
        except Exception as e:
            self.logger.error(f"Error retrieving from Firestore: {e}")
            return None
    
    def list_responses(self, collection: str, limit: int = 100) -> list:
        """List recent Notion responses."""
        try:
            docs = self.db.collection(collection)\
                .order_by('timestamp', direction=firestore.Query.DESCENDING)\
                .limit(limit)\
                .stream()
            return [doc.to_dict() for doc in docs]
        except Exception as e:
            self.logger.error(f"Error listing from Firestore: {e}")
            return []
    
    def delete_response(self, collection: str, doc_id: str) -> bool:
        """Delete a stored Notion response."""
        try:
            self.db.collection(collection).document(doc_id).delete()
            return True
        except Exception as e:
            self.logger.error(f"Error deleting from Firestore: {e}")
            return False 