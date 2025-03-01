#!/usr/bin/env python3
"""
Test transaction field handling.
"""

import pandas as pd

# Sample transactions
transactions = [
    {"date": "2023-01-01", "description": "GROCERY STORE", "amount": -45.67},
    {"date": "2023-01-02", "description": "UBER RIDE", "amount": -12.50},
    {"date": "2023-01-03", "description": "SALARY DEPOSIT", "amount": 2000.00}
]

# Convert to DataFrame
df = pd.DataFrame(transactions)
print("Input transactions:")
print(df)

# Mock categories dictionary
mock_categories = {
    'supermarket': 'Groceries',
    'grocery': 'Groceries',
    'food': 'Groceries',
    'uber': 'Transportation', 
    'taxi': 'Transportation',
    'transport': 'Transportation',
    'travel': 'Transportation',
    'salary': 'Income',
    'deposit': 'Income',
    'payroll': 'Income',
    'restaurant': 'Dining',
    'cafe': 'Dining',
    'coffee': 'Dining',
    'rent': 'Housing',
    'mortgage': 'Housing',
    'utilities': 'Housing'
}

print("\nTesting field handling...")
for idx, row in df.iterrows():
    # Check both possible description field names
    desc = str(row.get('transaction_description', row.get('description', ''))).lower()
    amount = float(row.get('amount', 0))
    
    # Determine category based on keywords and amount
    category = None
    highest_confidence = 0.75  # Default confidence
    
    # Check for matches in keywords
    for keyword, cat in mock_categories.items():
        if keyword in desc:
            category = cat
            highest_confidence = 0.9
            break
    
    # If no match found, use amount to determine category
    if not category:
        if amount > 0:
            category = 'Income'
            highest_confidence = 0.85
        else:
            # Default to most common category
            category = 'Other'
            highest_confidence = 0.65
    
    print(f"Transaction: {desc}, Amount: {amount}, Category: {category}, Confidence: {highest_confidence:.2f}")