import unittest
from unittest.mock import patch, MagicMock
import os
import sys
import json
import flask

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import main

class TestMain(unittest.TestCase):
    
    def setUp(self):
        # Create a Flask test app
        self.app = flask.Flask(__name__)
        self.app.testing = True
        self.context = self.app.test_request_context()
        self.context.push()
    
    def tearDown(self):
        self.context.pop()
    
    @patch('main.TransactionPredictor')
    def test_infer_category_valid_request(self, MockPredictor):
        # Mock predictor setup
        mock_predictor_instance = MockPredictor.return_value
        mock_predictor_instance.predict.return_value = [
            {"id": "1", "category": "Groceries", "confidence": 0.85},
            {"id": "2", "category": "Income", "confidence": 0.92}
        ]
        main.predictor = mock_predictor_instance
        
        # Create test request
        with self.app.test_request_context(
            '/infer-category',
            method='POST',
            json={
                "transactions": [
                    {"id": "1", "dateOp": "2023-01-01", "transaction_description": "GROCERY STORE", "amount": -50.00},
                    {"id": "2", "dateOp": "2023-01-02", "transaction_description": "SALARY DEPOSIT", "amount": 2000.00}
                ]
            }
        ):
            # Call the function
            response = main.infer_category(flask.request)
            
            # Parse the response
            response_body, status_code, headers = response
            response_data = json.loads(response_body)
            
            # Assert response structure
            self.assertEqual(status_code, 200)
            self.assertTrue(response_data['success'])
            self.assertEqual(len(response_data['results']), 2)
            self.assertIn('request_id', response_data)
    
    @patch('main.TransactionPredictor')
    def test_infer_category_no_transactions(self, MockPredictor):
        # Mock predictor setup
        mock_predictor_instance = MockPredictor.return_value
        main.predictor = mock_predictor_instance
        
        # Create test request with no transactions
        with self.app.test_request_context(
            '/infer-category',
            method='POST',
            json={"transactions": []}
        ):
            # Call the function
            response = main.infer_category(flask.request)
            
            # Parse the response
            response_body, status_code, headers = response
            response_data = json.loads(response_body)
            
            # Assert error response
            self.assertEqual(status_code, 400)
            self.assertFalse(response_data['success'])
            self.assertIn('error', response_data)
    
    @patch('main.TransactionPredictor')
    def test_infer_category_exception(self, MockPredictor):
        # Mock predictor to raise exception
        mock_predictor_instance = MockPredictor.return_value
        mock_predictor_instance.predict.side_effect = Exception("Test error")
        main.predictor = mock_predictor_instance
        
        # Create test request
        with self.app.test_request_context(
            '/infer-category',
            method='POST',
            json={
                "transactions": [
                    {"id": "1", "dateOp": "2023-01-01", "transaction_description": "GROCERY STORE", "amount": -50.00}
                ]
            }
        ):
            # Call the function
            response = main.infer_category(flask.request)
            
            # Parse the response
            response_body, status_code, headers = response
            response_data = json.loads(response_body)
            
            # Assert error response
            self.assertEqual(status_code, 500)
            self.assertFalse(response_data['success'])
            self.assertIn('error', response_data)
            self.assertEqual(response_data['error'], "Test error")

if __name__ == '__main__':
    unittest.main()