import pandas as pd
import os
import sys
import json
import time
from dotenv import load_dotenv

# Add parent directory to sys.path
sys.path.append('..')
from predictor import TransactionPredictor

def test_transaction_prediction(predictor, transactions, test_name="Basic Prediction Test"):
    """Test transaction prediction functionality"""
    print(f"\n=== {test_name} ===")
    
    print(f"Testing with {len(transactions)} transactions...")
    for i, t in enumerate(transactions, 1):
        print(f"{i}. {t['transaction_description']} (Amount: {t['amount']})")
    
    # Get predictions
    start_time = time.time()
    try:
        results = predictor.predict(transactions)
        end_time = time.time()
        
        print(f"\nPrediction completed in {end_time - start_time:.2f} seconds")
        
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
        
        return True, results
            
    except Exception as e:
        print(f"Error during prediction: {str(e)}")
        import traceback
        traceback.print_exc()
        return False, None

def prepare_test_data(csv_path, num_samples=5, delimiter=';'):
    """Load and prepare test data from CSV file"""
    # Load test data
    print(f"\nLoading test data from {csv_path}...")
    test_df = pd.read_csv(csv_path, sep=delimiter)
    print(f"Loaded {len(test_df)} total records")
    
    # Take sample transactions
    test_df = test_df.head(num_samples)
    
    # Prepare transactions in the expected format
    transactions = []
    for _, row in test_df.iterrows():
        transaction = {
            'transaction_description': row['transaction_description'] if 'transaction_description' in row.index else row.get('description', 'Unknown'),
            'amount': row['amount'] if 'amount' in row.index else 0,
            'dateOp': row['dateOp'] if 'dateOp' in row.index else str(pd.Timestamp.now().date())
        }
        transactions.append(transaction)
    
    return transactions

def test_edge_cases(predictor):
    """Test edge cases with unusual transaction descriptions"""
    print("\n=== Edge Case Tests ===")
    
    test_cases = [
        {
            'transaction_description': '',  # Empty description
            'amount': -10.0,
            'dateOp': '2023-01-01'
        },
        {
            'transaction_description': 'VERY LONG TRANSACTION DESCRIPTION WITH MANY CHARACTERS AND SPECIAL SYMBOLS !@#$%^&*()_+-=[]{}|;:",./<>?',
            'amount': -999999.99,  # Very large amount
            'dateOp': '2023-01-02'
        },
        {
            'transaction_description': None,  # None description
            'amount': 0,  # Zero amount
            'dateOp': '2023-01-03'
        },
        {
            'transaction_description': '123456789',  # Only numbers
            'amount': 0.01,  # Very small amount
            'dateOp': '2023-01-04'
        },
        {
            'transaction_description': 'Unicode characters: 你好 안녕하세요 Здравствуйте',  # Unicode characters
            'amount': -50.0,
            'dateOp': '2023-01-05'
        }
    ]
    
    # Create a display version of the test cases with truncated descriptions
    print(f"Testing with {len(test_cases)} edge case transactions...")
    for i, t in enumerate(test_cases, 1):
        desc = t['transaction_description']
        if desc is None:
            display_desc = "None"
        elif len(str(desc)) > 50:
            display_desc = str(desc)[:47] + "..."
        else:
            display_desc = str(desc)
        print(f"{i}. {display_desc} (Amount: {t['amount']})")
    
    # Run the prediction
    return test_transaction_prediction(predictor, test_cases, "Edge Cases Test")

def test_model_initialization(model_dir, use_mock=True, use_gcs=False):
    """Test model initialization"""
    print("\n=== Model Initialization Test ===")
    
    # Initialize predictor
    start_time = time.time()
    print("Initializing predictor...")
    predictor = TransactionPredictor(
        model_dir=model_dir,
        use_mock=use_mock,
        use_gcs=use_gcs
    )
    
    try:
        predictor.initialize()
        end_time = time.time()
        print(f"Initialization completed in {end_time - start_time:.2f} seconds")
        return True, predictor
    except Exception as e:
        print(f"Error during initialization: {str(e)}")
        import traceback
        traceback.print_exc()
        return False, None

def main():
    # Load environment variables from test env file
    load_dotenv('../.env.test')
    print("Environment variables loaded")
    
    # Define model directory
    model_dir = "../models/tabpfn-client"
    
    # Test 1: Model Initialization
    init_success, predictor = test_model_initialization(model_dir)
    if not init_success:
        print("Model initialization failed. Aborting tests.")
        return
    
    # Test 2: Basic Transaction Prediction
    transactions = prepare_test_data('../../data/test.csv', num_samples=5)
    basic_success, basic_results = test_transaction_prediction(predictor, transactions)
    
    # Test 3: Extended Transaction Prediction
    transactions_extended = prepare_test_data('../../data/test.csv', num_samples=10)
    extended_success, extended_results = test_transaction_prediction(
        predictor, 
        transactions_extended, 
        "Extended Prediction Test"
    )
    
    # Test 4: Edge Cases
    edge_success, edge_results = test_edge_cases(predictor)
    
    # Summary
    print("\n=== Test Summary ===")
    print(f"Model Initialization: {'✓ PASSED' if init_success else '✗ FAILED'}")
    print(f"Basic Transaction Prediction: {'✓ PASSED' if basic_success else '✗ FAILED'}")
    print(f"Extended Transaction Prediction: {'✓ PASSED' if extended_success else '✗ FAILED'}")
    print(f"Edge Cases: {'✓ PASSED' if edge_success else '✗ FAILED'}")
    
    overall_status = all([init_success, basic_success, extended_success, edge_success])
    print(f"\nOverall Test Status: {'✓ PASSED' if overall_status else '✗ FAILED'}")

if __name__ == "__main__":
    main() 