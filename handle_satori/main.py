from packages.Firestore import Firestore
from packages.storage import GCSStorage
from packages.Logging import CloudLogger
from datetime import datetime

class Card:
    """A class to handle card creation and management in Firestore.
    
    This class processes different types of cards (startups, cofounders, memos) from CSV files
    and stores them in Firestore collections. It's triggered by Cloud Storage events.
    
    Attributes:
        request (str): The name of the file that triggered the event
        db (firestore.Client): Firestore client instance
        storage (GCSStorage): Google Cloud Storage client instance
        logger (CloudLogger): Logger instance for monitoring
        data (list): Processed data from CSV file (for startups)
    """
    
    def __init__(self, request):
        """Initialize the Card processor.
        
        Args:
            request (str): The name of the file that triggered the event
        """
        self.request = request
        self.db = Firestore(database='memory-bank').client
        self.storage = GCSStorage(
            bucket_name="fuze-subscriptions",  # Replace with your bucket name
            project_id="digital-africa-fuze"
        )
        self.logger = CloudLogger("CardProcessor", prefix="card_processor")
        if 'startups' in request:
            data = self.storage.read_csv(request)
            self.data = data.to_dict(orient='records')[1:]

    def cofounder_card(self):
        """Process and store cofounder data in Firestore.
        
        Reads cofounder data from CSV and creates documents in the 'cofounders' collection.
        Each document contains cofounder details and metadata.
        
        Returns:
            tuple: (status_code, message) indicating success or failure
        """
        collection_name = 'cofounders'
        try:
            self.logger.info(f"Processing cofounder data from {self.request}")
            data = self.storage.read_csv(self.request)
            cofounder_documents = data.to_dict(orient='records')[1:]
            cofounder_documents = [
                {
                    "payload": {
                        'id_founder': record['id_founder'],
                        'cofounder_first_name': record['cofounder_first_name'],
                        'cofounder_last_name': record['cofounder_last_name'],
                        'cofounder_nationality': record['cofounder_nationality'],
                        'cofounder_email': record['cofounder_email'],
                        'cofounder_gender': record['cofounder_gender'],
                        'satori_id': record['id_startup']
                    },
                    "execution_status": "not started",
                    'source_file': self.request,
                    "timestamp": datetime.now().isoformat(),
                    "satori_id": record['id_startup']
                } 
                for record in cofounder_documents
            ]
            
            self.logger.info(f"Creating {len(cofounder_documents)} cofounder documents")
            
            # Use batch write for better performance
            batch = self.db.batch()
            for card in cofounder_documents:
                doc_ref = self.db.collection(collection_name).document(card['satori_id'])
                batch.set(doc_ref, card)
                self.logger.debug(f"Added cofounder document for satori_id: {card['satori_id']} to batch")
                
            # Commit the batch
            batch.commit()
            self.logger.info("Successfully committed all cofounder documents in batch")
            return 200, "Cofounder card created successfully"
        except Exception as e:
            self.logger.error(f"Error processing cofounder data: {str(e)}", extra={"file": self.request})
            raise e

    def startups_card(self):
        """Process and store startup data in Firestore.
        
        Creates documents in the 'startups' collection with startup details and metadata.
        Uses pre-loaded data from the CSV file.
        
        Returns:
            tuple: (status_code, message) indicating success or failure
        """
        collection_name = 'startups'
        collection = self.db.collection(collection_name)
        try:
            self.logger.info(f"Processing startup data from {self.request}")
            startups_documents = [
                {
                    "payload": {
                        'satori_id': record['id'], 
                        'country_operation': record['country_operation'], 
                        'country_of_incorporation': record['country_of_incorporation'], 
                        'website': record['website'],
                        'sector': record['line_of_business.1'],
                        'sector_freetext': record['line_of_business.2'], 
                        'Award': record['what_awards_have_you_received_for_your_startup'],
                        'Innovation': record['innovation_description'],
                        'Problem Solved': record['problem_description'],
                        'Solution Provided': record['project_description'],
                        'Technologie': record['what_technologies_will_you_use'],
                        'date_updated': record['date_updated'],     
                        'date_application': record['date_updated'],
                        'creation_date': record['creation_date'], 
                        'status': record['status'],
                        'Startups': record['name']
                    },
                    "execution_status": "pending",
                    'source_file': self.request,
                    "timestamp": datetime.now().isoformat(),
                    "satori_id": record['id']
                } 
                for record in self.data
            ]
            
            self.logger.info(f"Creating {len(startups_documents)} startup documents")
            
            # Use batch write for better performance
            batch = self.db.batch()
            for card in startups_documents:
                doc_ref = collection.document(card['satori_id'])
                batch.set(doc_ref, card)
                self.logger.debug(f"Added startup document for satori_id: {card['satori_id']} to batch")
                
            # Commit the batch
            batch.commit()
            self.logger.info("Successfully committed all startup documents in batch")
            return 200, "Startups card created successfully"
        except Exception as e:
            self.logger.error(f"Error processing startup data: {str(e)}", extra={"file": self.request})
            raise e

    def memo_card(self):
        """Process and store memo data in Firestore.
        
        Creates documents in the 'memos' collection with memo details and metadata.
        Uses pre-loaded data from the CSV file.
        
        Returns:
            tuple: (status_code, message) indicating success or failure
        """
        collection_name = 'memo'
        collection = self.db.collection(collection_name)
        try:
            self.logger.info(f"Processing memo data from {self.request}")
            memos_documents = [
                {
                    "payload": {
                        'satori_id': record['id'], 
                        'kbis': record['kbis'], 
                        'logo': record['logo'],
                        'pitch_deck': record['pitch_deck'],
                        'youtube_link_of_your_pitch': record['youtube_link_of_your_pitch']
                    },
                    "execution_status": "pending",
                    'source_file': self.request,
                    "timestamp": datetime.now().isoformat(),
                    "satori_id": record['id']
                } 
                for record in self.data
            ]
            
            self.logger.info(f"Creating {len(memos_documents)} memo documents")
            
            # Use batch write for better performance
            batch = self.db.batch()
            for card in memos_documents:
                doc_ref = collection.document(card['satori_id'])
                batch.set(doc_ref, card)
                self.logger.debug(f"Added memo document for satori_id: {card['satori_id']} to batch")
                
            # Commit the batch
            batch.commit()
            self.logger.info("Successfully committed all memo documents in batch")
            return 200, "Memo card created successfully"
        except Exception as e:
            self.logger.error(f"Error processing memo data: {str(e)}", extra={"file": self.request})
            raise e

def handle_satori(event, context):
    """Cloud Function entry point triggered by Cloud Storage events.
    
    Processes uploaded CSV files and creates corresponding cards in Firestore.
    Supports three types of files: startups, cofounders, and memos.
    
    Args:
        event: The event data from Cloud Storage trigger (can be CloudEvent or dict)
        context: Metadata for the event (unused)
        
    Returns:
        None
    """
    # Handle both CloudEvent and dict formats for Gen2 Cloud Functions
    if hasattr(event, 'data'):
        # CloudEvent format
        data = event.data
    else:
        # Dict format (direct event data)
        data = event
    
    request_name = data['name']
    logger = CloudLogger("GCSFunction", prefix="gcs_function")
    logger.info(f"Processing file: {request_name} in bucket: {data['bucket']}")
    
    card = Card(request_name)
    try:   
        if 'startups' in request_name:
            logger.info("Processing startups file")
            card.startups_card()
            card.memo_card()
            logger.info("Successfully processed startups and memo cards")
        elif 'cofounder' in request_name:
            logger.info("Processing cofounder file")
            card.cofounder_card()
            logger.info("Successfully processed cofounder cards")
        else: 
            error_msg = f"Invalid file type: {request_name}"
            logger.error(error_msg)
            raise ValueError(error_msg)
    except Exception as e:
        logger.error(f"Error processing file: {str(e)}", extra={"file": request_name})
        raise e