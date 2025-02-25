import requests
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_function():
    url = "https://europe-west1-my-projects-406017.cloudfunctions.net/infer-category-v2"
    payload = {
        "transactions": [
            {
                "id": "test1",
                "dateOp": "01/03/2024",
                "amount": -75.5,
                "transaction_description": "CARREFOUR MARKET"
            },
            {
                "id": "test2",
                "dateOp": "01/03/2024",
                "amount": -30.0,
                "transaction_description": "RANDOM SHOP THAT DOESNT MATCH ANY MOCK KEYWORDS"
            },
            {
                "id": "test3",
                "dateOp": "01/03/2024",
                "amount": -50.0,
                "transaction_description": "SNCF PARIS"
            }
        ]
    }
    
    try:
        logger.info("Sending request to function...")
        logger.info(f"Payload: {json.dumps(payload, indent=2)}")
        
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        
        logger.info(f"Status Code: {response.status_code}")
        logger.info(f"Response: {json.dumps(response.json(), indent=2)}")
        
        # Analyze if mock predictions are being used
        results = response.json().get('results', [])
        logger.info("\nAnalysis of predictions:")
        for result in results:
            logger.info(f"\nTransaction: {result['description']}")
            logger.info(f"Category: {result['predicted_category']}")
            logger.info(f"Confidence: {result['confidence']:.2%}")
            
            # Check for signs of mock predictions
            is_likely_mock = False
            if result['confidence'] >= 0.85 and result['confidence'] <= 0.95:
                is_likely_mock = True  # Mock predictions always have confidence in this range
            if "CARREFOUR" in result['description'].upper() and result['predicted_category'] == "Alimentation":
                is_likely_mock = True  # Mock has hardcoded rules for these
            if "SNCF" in result['description'].upper() and result['predicted_category'] == "Transport":
                is_likely_mock = True
                
            logger.info(f"Likely using mock: {is_likely_mock}")
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Error making request: {str(e)}")
        if hasattr(e.response, 'text'):
            logger.error(f"Response text: {e.response.text}")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")

if __name__ == "__main__":
    test_function() 