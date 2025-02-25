import pandas as pd
import os
import sys
import json
from dotenv import load_dotenv

# Add parent directory to sys.path
sys.path.append('..')
from predictor import TransactionPredictor

def main():
    # Load environment variables from test env file
    load_dotenv('../.env.test')
    print("Environment variables loaded")
    
    # Define model directory
    model_dir = "../models/tabpfn-client"
    
    # Initialize predictor with mock data to avoid API calls
    print("Initializing predictor...")
    predictor = TransactionPredictor(
        model_dir=model_dir,
        use_mock=True,  # Use mock predictions
        use_gcs=False   # Don't use Google Cloud Storage
    )
    predictor.initialize()
    
    # Load test data
    print("\nLoading test data...")
    test_df = pd.read_csv('../../data/test.csv', sep=';')  # Using semicolon separator
    print(f"Loaded {len(test_df)} test records")
    
    # Take first 10 transactions as a sample
    test_df = test_df.head(10)
    
    # Prepare transactions in the expected format
    transactions = []
    for _, row in test_df.iterrows():
        transaction = {
            'transaction_description': row['transaction_description'] if 'transaction_description' in row.index else row.get('description', 'Unknown'),
            'amount': row['amount'] if 'amount' in row.index else 0,
            'dateOp': row['dateOp'] if 'dateOp' in row.index else str(pd.Timestamp.now().date())
        }
        transactions.append(transaction)
    
    print("\nTesting with transactions:")
    for i, t in enumerate(transactions, 1):
        print(f"{i}. {t['transaction_description']} (Amount: {t['amount']})")
    
    # Get predictions
    try:
        results = predictor.predict(transactions)
        
        # Print the structure of the results to debug
        print("\nResults structure:")
        print(type(results))
        
        # Display results based on structure
        print("\nPredictions:")
        if isinstance(results, dict):
            print(f"Success: {results.get('success', False)}")
            
            if 'results' in results and isinstance(results['results'], list):
                predictions = results['results']
                print(f"\nGot {len(predictions)} predictions:")
                
                for i, prediction in enumerate(predictions):
                    print(f"\nTransaction {i+1}:")
                    if prediction:  # Check if prediction is not None or empty
                        for key, value in prediction.items():
                            # Format confidence as percentage if it's a numeric value between 0 and 1
                            if key == 'confidence' and isinstance(value, (int, float)) and 0 <= value <= 1:
                                print(f"  {key}: {value:.2%}")
                            else:
                                print(f"  {key}: {value}")
                    else:
                        print("  No prediction data available")
            
            if 'errors' in results and results['errors']:
                print("\nErrors:")
                for error in results['errors']:
                    print(f"- {error}")
                
            if 'total_errors' in results:
                print(f"\nTotal errors: {results['total_errors']}")
                
        elif isinstance(results, list):
            for i, result in enumerate(results):
                print(f"\nTransaction {i+1}:")
                if isinstance(result, dict):
                    for key, value in result.items():
                        print(f"  {key}: {value}")
                else:
                    print(f"  {result}")
            
    except Exception as e:
        print(f"Error during prediction: {str(e)}")
        import traceback
        traceback.print_exc()
        return

if __name__ == "__main__":
    main() 