import json
import logging
import pandas as pd
import pickle
import tempfile
from google.cloud import storage
from predictor import preprocess_inference_data, validate_transformers
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_transformers():
    """Load transformers from GCS."""
    try:
        # GCS settings
        bucket_name = os.getenv('GCS_BUCKET', 'mybucket_ben_becker11')
        blob_name = 'models/tabpfn-client/transformers.pkl'
        
        # Create temp directory
        temp_dir = tempfile.mkdtemp()
        local_path = os.path.join(temp_dir, 'transformers.pkl')
        
        # Download from GCS
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(blob_name)
        blob.download_to_filename(local_path)
        
        # Load transformers
        with open(local_path, 'rb') as f:
            transformers = pickle.load(f)
        
        # Validate transformers
        if not validate_transformers(transformers):
            logger.error("Invalid transformers loaded from GCS")
            return None
            
        logger.info("Successfully loaded and validated transformers")
        return transformers
        
    except Exception as e:
        logger.error(f"Failed to load transformers: {str(e)}")
        return None

def test_preprocessing():
    try:
        # Load transformers
        logger.info("Loading transformers...")
        transformers = load_transformers()
        
        # Test data
        transactions = [{
            "id": "test1",
            "dateOp": "01/03/2024",
            "amount": -50.0,
            "transaction_description": "SNCF PARIS"
        }]
        
        logger.info("Test payload:")
        logger.info(json.dumps(transactions, indent=2))
        
        # Convert to DataFrame
        df = pd.DataFrame(transactions)
        logger.info("\nInput DataFrame:")
        logger.info(f"\n{df}")
        
        # Run preprocessing with transformers
        logger.info("\nRunning preprocessing with transformers...")
        features = preprocess_inference_data(df, transformers=transformers)
        
        # Print feature information
        logger.info("\nFeature columns and values:")
        for col in features.columns:
            logger.info(f"- {col}: {features[col].values[0]}")
        
        logger.info("\nComplete features DataFrame:")
        logger.info(f"\n{features}")
        
        # Verify text embedding columns
        embedding_cols = [col for col in features.columns if col.startswith('desc_emb_')]
        logger.info(f"\nNumber of text embedding columns: {len(embedding_cols)}")
        logger.info(f"Text embedding columns: {embedding_cols}")
        
    except Exception as e:
        logger.error(f"Error during preprocessing: {str(e)}", exc_info=True)

if __name__ == "__main__":
    test_preprocessing() 