from tabpfn_client import init, set_access_token
import logging
import json
import requests

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_capacity():
    try:
        # Initialize TabPFN client with the correct token
        token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyIjoiMTA5M2IxZjYtZjMxZi00MGU4LWE3Y2YtZjFkYzQ2ZTRlNDExIiwiZXhwIjoxNzY4MzEyMDk4fQ.p_zt6eCClfPdqsxgE4sUk5dL5co9tDRKkzuryZ5wo8k"
        set_access_token(token)
        init(use_server=True)
        
        logger.info("TabPFN client initialized with token")
        
        # Make a small test request
        url = "https://europe-west1-my-projects-406017.cloudfunctions.net/infer-category-v2"
        test_payload = {
            "transactions": [{
                "id": "test1",
                "dateOp": "01/03/2024",
                "amount": "-50.0",
                "transaction_description": "SNCF PARIS"
            }]
        }
        
        logger.info("Sending test request to check capacity...")
        response = requests.post(url, json=test_payload)
        
        # Print response status and headers
        logger.info(f"Response status code: {response.status_code}")
        logger.info("\nResponse headers:")
        for header, value in response.headers.items():
            if header.lower().startswith('x-ratelimit'):
                logger.info(f"{header}: {value}")
        
        # Parse and print response body
        response_data = response.json()
        logger.info("\nResponse body:")
        logger.info(json.dumps(response_data, indent=2))
        
        # Check for rate limit error
        if response_data.get('results', {}).get('error') == 'UNKNOWN_ERROR' and 'Prediction API Limit Reached' in str(response_data):
            logger.info("\nAPI RATE LIMIT REACHED!")
            # Try to extract reset time
            message = str(response_data.get('results', {}).get('message', ''))
            if 'try again after' in message:
                reset_time = message.split('try again after')[1].split('UTC')[0].strip()
                logger.info(f"Limit will reset at: {reset_time} UTC")
        else:
            logger.info("\nAPI CAPACITY AVAILABLE - You can make predictions!")
        
    except Exception as e:
        logger.error(f"Error testing capacity: {str(e)}")

if __name__ == "__main__":
    test_capacity() 