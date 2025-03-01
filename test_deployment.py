#!/usr/bin/env python3
"""
Test script to verify the TabPFN cloud function deployment
"""

import requests
import json
import logging
import argparse
import sys
import time
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_function(url, test_data=None, verbose=False):
    """Test the deployed cloud function with sample transaction data."""
    
    if test_data is None:
        # Default test data
        test_data = {
            "transactions": [
                {
                    "date": "2023-01-01",
                    "description": "GROCERY STORE",
                    "amount": -45.67
                },
                {
                    "date": "2023-01-02", 
                    "description": "UBER RIDE",
                    "amount": -12.50
                },
                {
                    "date": "2023-01-03",
                    "description": "SALARY DEPOSIT",
                    "amount": 2000.00
                }
            ]
        }
    
    logger.info(f"Testing function at URL: {url}")
    if verbose:
        logger.info(f"Test data: {json.dumps(test_data, indent=2)}")
    
    try:
        start_time = time.time()
        response = requests.post(
            url,
            headers={"Content-Type": "application/json"},
            data=json.dumps(test_data)
        )
        end_time = time.time()
        
        # Check response
        logger.info(f"Response status code: {response.status_code}")
        logger.info(f"Response time: {end_time - start_time:.2f} seconds")
        
        if response.status_code == 200:
            result = response.json()
            if verbose:
                logger.info(f"Full response: {json.dumps(result, indent=2)}")
            
            # Check for success flag
            if result.get("success", False):
                logger.info("✅ Function returned success response")
                logger.info(f"Mode: {result.get('mode', 'unknown')}")
                # Handle nested total_processed
                total_processed = result.get('total_processed', 0)
                if isinstance(result.get('results'), dict):
                    total_processed = result.get('results', {}).get('total_processed', total_processed)
                
                logger.info(f"Processed {total_processed} transactions")
                
                # Check for predicted categories
                # Handle nested results structure
                results_data = result.get("results", [])
                if isinstance(results_data, dict) and "results" in results_data:
                    results_data = results_data.get("results", [])
                
                for i, res in enumerate(results_data):
                    logger.info(f"Transaction {i+1}: {res.get('description', '')} → {res.get('predicted_category', 'unknown')} (confidence: {res.get('confidence', 0):.2f})")
                
                return True
            else:
                logger.error("❌ Function returned failure response")
                logger.error(f"Errors: {result.get('errors', [])}")
                return False
        else:
            logger.error(f"❌ Failed with status code {response.status_code}")
            logger.error(f"Response: {response.text}")
            return False
            
    except requests.RequestException as e:
        logger.error(f"❌ Request failed: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"❌ Unexpected error: {str(e)}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Test the TabPFN cloud function deployment")
    parser.add_argument("--url", required=True, help="URL of the deployed cloud function")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show detailed output")
    parser.add_argument("--data", "-d", help="Path to JSON file with test data (optional)")
    
    args = parser.parse_args()
    
    # Load test data from file if provided
    test_data = None
    if args.data:
        try:
            with open(args.data, 'r') as f:
                test_data = json.load(f)
            logger.info(f"Loaded test data from {args.data}")
        except Exception as e:
            logger.error(f"Failed to load test data: {str(e)}")
            return 1
    
    # Run the test
    success = test_function(args.url, test_data, args.verbose)
    
    # Return appropriate exit code
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())