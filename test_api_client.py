#!/usr/bin/env python3
"""
Test TabPFN client API functionality locally before deploying.
"""

import os
import json
import logging
import pandas as pd
import numpy as np
from dotenv import load_dotenv
from tabpfn_client import TabPFNClassifier, set_access_token

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def test_tabpfn_api():
    """Test TabPFN API client with sample transactions."""
    
    # Set token - use the same token we have in .env.yaml
    # Read token from .env.yaml
    token = None
    try:
        with open('.env.yaml', 'r') as f:
            for line in f:
                if 'TABPFN_API_TOKEN' in line:
                    token = line.split('"')[1]
                    break
    except Exception as e:
        logger.error(f"Error reading token from .env.yaml: {str(e)}")
    
    if not token:
        logger.error("TABPFN_API_TOKEN not found in .env.yaml")
        return False
    
    logger.info(f"Using TabPFN API token: {token[:10]}...")
    set_access_token(token)
    
    # Sample transactions
    transactions = [
        {"date": "2023-01-01", "description": "GROCERY STORE", "amount": -45.67},
        {"date": "2023-01-02", "description": "UBER RIDE", "amount": -12.50},
        {"date": "2023-01-03", "description": "SALARY DEPOSIT", "amount": 2000.00}
    ]
    
    # Convert to DataFrame
    df = pd.DataFrame(transactions)
    logger.info(f"Input transactions:\n{df}")
    
    try:
        # Create TabPFNClassifier instance
        logger.info("Creating TabPFNClassifier instance...")
        classifier = TabPFNClassifier()
        
        # Prepare features
        X = []
        for _, row in df.iterrows():
            feature = [
                str(row.get('description', '')),
                float(row.get('amount', 0))
            ]
            X.append(feature)
        
        X = np.array(X, dtype=object)
        logger.info(f"Features shape: {X.shape}")
        
        # For prediction without training, we need dummy targets
        dummy_y = np.zeros(len(X))
        
        # Fit with the dummy data
        logger.info("Fitting classifier...")
        classifier.fit(X, dummy_y)
        
        # Get predictions
        logger.info("Getting predictions...")
        categories = classifier.predict(X)
        probas = classifier.predict_proba(X)
        
        # Format results
        results = []
        for i, (category, proba) in enumerate(zip(categories, probas)):
            confidence = float(max(proba))
            result = {
                'transaction': transactions[i],
                'predicted_category': str(category),
                'confidence': confidence
            }
            results.append(result)
        
        # Print results
        logger.info("Results:")
        for result in results:
            logger.info(f"Transaction: {result['transaction']['description']}, "
                       f"Amount: {result['transaction']['amount']}, "
                       f"Category: {result['predicted_category']}, "
                       f"Confidence: {result['confidence']:.2f}")
        
        return True
    
    except Exception as e:
        logger.error(f"Error in TabPFN API test: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_tabpfn_api()
    if success:
        logger.info("TabPFN API test completed successfully")
    else:
        logger.error("TabPFN API test failed")