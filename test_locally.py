#!/usr/bin/env python
"""
Local testing script for TabPFN Cloud Function
"""
import json
import requests
from flask import Flask, request, jsonify
import functions_framework
from main import infer_category

app = Flask(__name__)

# Create a test endpoint that runs the function locally
@app.route('/test', methods=['POST'])
def test_function():
    # Forward the request to our function
    response = infer_category(request)
    
    # If it's a tuple (which cloud functions return), extract components
    if isinstance(response, tuple):
        body, status_code, headers = response
        return body, status_code, headers
    return response

# Create a test client
@app.route('/send_test', methods=['GET'])
def send_test():
    # Example transactions
    test_data = {
        "transactions": [
            {
                "id": "test1",
                "dateOp": "2023-04-15",
                "transaction_description": "PAYMENT *GROCERY STORE",
                "amount": -45.67
            },
            {
                "id": "test2",
                "dateOp": "2023-04-16",
                "transaction_description": "DIRECT DEPOSIT SALARY",
                "amount": 1200.00
            }
        ]
    }
    
    # Send test request to our local endpoint
    response = requests.post(
        'http://localhost:8080/test',
        json=test_data,
        headers={'Content-Type': 'application/json'}
    )
    
    # Format the response
    return f"""
    Status: {response.status_code}
    
    Response:
    {json.dumps(response.json(), indent=2)}
    """

if __name__ == '__main__':
    print("Starting local test server...")
    print("- Test endpoint: http://localhost:8080/test")
    print("- Send test data: http://localhost:8080/send_test")
    app.run(port=8080, debug=True)