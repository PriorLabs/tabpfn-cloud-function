import unittest
import pandas as pd
import os
from predictor import TransactionPredictor
from tabpfn_client import init
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging for tests
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestTransactionPredictor(unittest.TestCase):
    def setUp(self):
        # Use the actual model directory where the trained models are stored
        self.local_model_dir = os.path.join("cloud_function", "models", "tabpfn-client")
        self.gcs_model_dir = "models/tabpfn-client"  # GCS path
        self.gcs_bucket = os.getenv('GCS_BUCKET')
        logger.info(f"Using local model directory: {self.local_model_dir}")
        if self.gcs_bucket:
            logger.info(f"Using GCS bucket: {self.gcs_bucket}")
            
        # Sample test data
        self.test_transactions = [
            {
                "id": "1",
                "dateOp": "01/03/2024",
                "amount": -50.0,
                "transaction_description": "SNCF PARIS"
            },
            {
                "id": "2",
                "dateOp": "02/03/2024",
                "amount": -75.5,
                "transaction_description": "CARREFOUR MARKET"
            },
            {
                "id": "3",
                "dateOp": "03/03/2024",
                "amount": -120.0,
                "transaction_description": "EDF FACTURE"
            }
        ]
        
    def test_mock_predictor(self):
        """Test the predictor in mock mode"""
        predictor = TransactionPredictor(self.local_model_dir, use_mock=True)
        predictor.initialize()
        
        results = predictor.predict(self.test_transactions)
        
        # Verify basic structure and content
        self.assertEqual(len(results), len(self.test_transactions))
        self.assertTrue(all('predicted_category' in r for r in results))
        self.assertTrue(all('confidence' in r for r in results))
        
        # Verify specific categories based on descriptions
        self.assertEqual(results[0]['predicted_category'], 'Transport')  # SNCF should be Transport
        self.assertEqual(results[1]['predicted_category'], 'Alimentation')  # CARREFOUR should be Alimentation
        self.assertEqual(results[2]['predicted_category'], 'Logement')  # EDF should be Logement
        
        # Verify confidence scores are in reasonable range
        self.assertTrue(all(0.8 <= r['confidence'] <= 1.0 for r in results))
        
        logger.info("Mock predictor test completed successfully")
        
    def test_local_tabpfn_predictor(self):
        """Test the TabPFN predictor with local models"""
        predictor = TransactionPredictor(self.local_model_dir, use_mock=False)
        predictor.initialize()
        
        results = predictor.predict(self.test_transactions)
        
        # Verify we get valid predictions
        self.assertEqual(len(results), len(self.test_transactions))
        self.assertTrue(all('predicted_category' in r for r in results))
        self.assertTrue(all('confidence' in r for r in results))
        
        # Log the predictions for inspection
        for result in results:
            logger.info(f"Local prediction for {result['description']}: {result['predicted_category']} (confidence: {result['confidence']:.2f})")
        
        logger.info("Local TabPFN predictor test completed successfully")
        
    @unittest.skipIf(not os.getenv('GCS_BUCKET'), "GCS_BUCKET not set")
    def test_gcs_tabpfn_predictor(self):
        """Test the TabPFN predictor with GCS models"""
        predictor = TransactionPredictor(
            self.gcs_model_dir,
            use_mock=False,
            use_gcs=True,
            bucket_name=self.gcs_bucket
        )
        predictor.initialize()
        
        results = predictor.predict(self.test_transactions)
        
        # Verify we get valid predictions
        self.assertEqual(len(results), len(self.test_transactions))
        self.assertTrue(all('predicted_category' in r for r in results))
        self.assertTrue(all('confidence' in r for r in results))
        
        # Log the predictions for inspection
        for result in results:
            logger.info(f"GCS prediction for {result['description']}: {result['predicted_category']} (confidence: {result['confidence']:.2f})")
        
        logger.info("GCS TabPFN predictor test completed successfully")

if __name__ == '__main__':
    unittest.main() 