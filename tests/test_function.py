import requests
import json
import pandas as pd
from main import infer_category
from flask import Request

def create_mock_request(transactions):
    """Create a mock request object with the given transactions."""
    class MockRequest:
        def __init__(self, json_data):
            self._json = json_data
            self.method = 'POST'
        
        def get_json(self):
            return self._json
    
    return MockRequest({'transactions': transactions})

def main():
    # Load some test transactions from test.csv
    print("Loading test transactions...")
    test_df = pd.read_csv('../data/test.csv', sep=';')
    
    # Take first 2 transactions as a sample (to avoid API limits)
    sample_transactions = []
    for _, row in test_df.head(2).iterrows():
        transaction = {
            'id': str(len(sample_transactions) + 1),
            'dateOp': row['dateOp'],
            'transaction_description': row['transaction_description'],
            'amount': row['amount'],
            'accountNum': row['accountNum']
        }
        sample_transactions.append(transaction)
    
    print(f"\nTesting with {len(sample_transactions)} transactions:")
    for t in sample_transactions:
        print(f"- {t['transaction_description']} ({t['amount']})")
    
    # Create mock request
    mock_request = create_mock_request(sample_transactions)
    
    # Call the function
    print("\nCalling cloud function...")
    try:
        response, status_code, headers = infer_category(mock_request)
        
        # Parse and display results
        print(f"\nStatus code: {status_code}")
        print("Headers:", headers)
        
        results = json.loads(response)
        
        if results['success']:
            print("\nPredictions:")
            for result in results['results']:
                print("\nTransaction Details:")
                print(f"ID: {result['transaction_id']}")
                print(f"Description: {result['description']}")
                print(f"Category: {result['predicted_category']}")
                print(f"Confidence: {result['confidence']:.2%}")
                print("-" * 50)
        else:
            print("\nError:")
            print(results.get('error', 'Unknown error'))
            
    except Exception as e:
        print(f"\nError executing cloud function: {str(e)}")

def test_function():
    url = "https://europe-west1-my-projects-406017.cloudfunctions.net/infer-category-v2"
    payload = {
        "transactions": [
            {
                "dateOp": "2025-02-18",
                "transaction_description": "UBER TRIP",
                "amount": -25.50
            }
        ]
    }
    
    response = requests.post(url, json=payload)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

if __name__ == "__main__":
    main()
    test_function() 
