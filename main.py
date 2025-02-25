import functions_framework
import os
from datetime import datetime
import json
import logging
from dotenv import load_dotenv
from predictor import TransactionPredictor
from google.cloud import storage
from google.api_core import retry

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Constants for GCS
GCS_BUCKET = os.getenv('GCS_BUCKET', 'your-bucket-name')
MODEL_PATH = "models/tabpfn-client"

# Global predictor instance
predictor = None

def initialize_predictor():
    """Initialize the global predictor instance."""
    global predictor
    if predictor is None:
        try:
            # Initialize predictor with GCS configuration
            use_mock = os.getenv('USE_MOCK', '').lower() == 'true'
            use_gcs = os.getenv('USE_GCS', '').lower() == 'true'
            
            predictor = TransactionPredictor(
                model_dir=MODEL_PATH,
                use_mock=use_mock,
                use_gcs=use_gcs,
                gcs_bucket=GCS_BUCKET
            )
            
            predictor.initialize()
            logger.info("Predictor initialization completed successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize predictor: {str(e)}")
            raise

@functions_framework.http
def infer_category(request):
    """HTTP Cloud Function to infer transaction category."""
    request_id = datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')
    logger.info(f"Processing request {request_id}")
    
    # Set CORS headers for the preflight request
    if request.method == 'OPTIONS':
        headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'POST',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Max-Age': '3600'
        }
        return ('', 204, headers)

    # Set CORS headers for the main request
    headers = {
        'Access-Control-Allow-Origin': '*',
        'Content-Type': 'application/json'
    }
    
    try:
        # Initialize predictor if needed
        if predictor is None:
            logger.info(f"[{request_id}] Initializing predictor...")
            initialize_predictor()
        
        # Get request data
        request_json = request.get_json()
        if not request_json:
            logger.warning(f"[{request_id}] No JSON data in request")
            return (json.dumps({
                'error': 'No JSON data provided',
                'success': False,
                'request_id': request_id
            }), 400, headers)
        
        if 'transactions' not in request_json:
            logger.warning(f"[{request_id}] No transactions in request data")
            return (json.dumps({
                'error': 'No transactions provided',
                'success': False,
                'request_id': request_id
            }), 400, headers)
        
        transactions = request_json['transactions']
        if not transactions:
            logger.warning(f"[{request_id}] Empty transactions list")
            return (json.dumps({
                'error': 'Empty transactions list',
                'success': False,
                'request_id': request_id
            }), 400, headers)
        
        logger.info(f"[{request_id}] Processing {len(transactions)} transactions")
        
        # Get predictions
        try:
            results = predictor.predict(transactions)
            
            response_data = {
                'success': True,
                'results': results,
                'request_id': request_id,
                'mode': 'mock' if predictor.use_mock else 'tabpfn'
            }
            
            logger.info(f"[{request_id}] Successfully processed {len(results)} transactions")
            return (json.dumps(response_data), 200, headers)
            
        except Exception as e:
            logger.error(f"[{request_id}] Error during prediction: {str(e)}")
            return (json.dumps({
                'error': str(e),
                'success': False,
                'request_id': request_id
            }), 500, headers)
            
    except Exception as e:
        logger.error(f"[{request_id}] Error in infer_category: {str(e)}")
        return (json.dumps({
            'error': str(e),
            'success': False,
            'request_id': request_id
        }), 500, headers) 