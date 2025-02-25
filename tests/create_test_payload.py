import json

test_payload = {
    "transactions": [
        {
            "id": "test1",
            "dateOp": "01/03/2024",
            "amount": "-50.0",
            "transaction_description": "SNCF PARIS"
        },
        {
            "id": "test2",
            "dateOp": "02/03/2024",
            "amount": "-35.5",
            "transaction_description": "CARREFOUR MARKET"
        }
    ]
}

with open('test_payload.json', 'w', encoding='utf-8') as f:
    json.dump(test_payload, f, indent=4) 