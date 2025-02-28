import unittest
from unittest.mock import patch, MagicMock
import os
import sys
import json

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from predictor import TransactionPredictor

class TestPredictor(unittest.TestCase):
    
    @patch('predictor.TransactionPredictor.load_models_from_local')
    def test_mock_predict(self, mock_load):
        """Test the predictor in mock mode"""
        # Setup
        predictor = TransactionPredictor(model_dir='mock/path', use_mock=True)
        predictor.initialize()
        
        # Test data
        transactions = [
            {"id": "1", "dateOp": "2023-01-01", "transaction_description": "GROCERY STORE", "amount": -50.00},
            {"id": "2", "dateOp": "2023-01-02", "transaction_description": "SALARY DEPOSIT", "amount": 2000.00},
        ]
        
        # Execute
        results = predictor.predict(transactions)
        
        # Assert
        self.assertEqual(len(results), 2)
        self.assertIn("category", results[0])
        self.assertIn("confidence", results[0])
        
        # Check mock categories based on pattern matching
        self.assertTrue(any(r["category"] == "Groceries" for r in results))
        
    @patch('predictor.requests.post')
    def test_tabpfn_api_predict(self, mock_post):
        """Test the predictor with mock TabPFN API response"""
        # Mock API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "predictions": [
                {"class": "Food", "probability": 0.85},
                {"class": "Income", "probability": 0.92}
            ]
        }
        mock_post.return_value = mock_response
        
        # Setup predictor with mock
        predictor = TransactionPredictor(model_dir='mock/path', use_mock=False)
        predictor.tabpfn_model = MagicMock()
        predictor.text_transformer = MagicMock()
        predictor.numeric_transformer = MagicMock()
        
        # Test data
        transactions = [
            {"id": "1", "dateOp": "2023-01-01", "transaction_description": "GROCERY STORE", "amount": -50.00},
            {"id": "2", "dateOp": "2023-01-02", "transaction_description": "SALARY DEPOSIT", "amount": 2000.00},
        ]
        
        # Execute with patched API call
        with patch.object(predictor, 'preprocess_transactions', return_value=(None, None)):
            results = predictor.predict(transactions)
        
        # Assert
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["category"], "Food")
        self.assertEqual(results[1]["category"], "Income")
        self.assertAlmostEqual(results[0]["confidence"], 0.85)
        self.assertAlmostEqual(results[1]["confidence"], 0.92)

if __name__ == '__main__':
    unittest.main()