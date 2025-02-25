import requests
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_endpoint():
    # Cloud Function URL
    url = "https://europe-west1-my-projects-406017.cloudfunctions.net/infer-category-v2"
    
    # Load test payload
    with open('test_payload.json', 'r') as f:
        payload = json.load(f)
    
    logger.info("Sending request to cloud function...")
    
    try:
        # Make the request
        response = requests.post(url, json=payload)
        
        # Check status code
        logger.info(f"Status code: {response.status_code}")
        
        # Print headers (including rate limit info)
        logger.info("Response headers:")
        for header, value in response.headers.items():
            if header.lower().startswith('x-ratelimit'):
                logger.info(f"{header}: {value}")
        
        # Print response
        logger.info("Response body:")
        logger.info(json.dumps(response.json(), indent=2))
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")

if __name__ == "__main__":
    test_endpoint() 