import requests
import json

def main():
    # Load test payload
    with open('test_payload.json', 'r') as f:
        payload = json.load(f)
    
    # Function URL
    url = 'https://europe-west1-my-projects-406017.cloudfunctions.net/infer_category'
    
    print(f"Sending request to: {url}\n")
    print(f"Payload:\n{json.dumps(payload, indent=2)}\n")
    
    # Send request
    try:
        response = requests.post(url, json=payload)
        print(f"Status Code: {response.status_code}\n")
        
        if response.status_code == 200:
            result = response.json()
            print("Response:")
            print(json.dumps(result, indent=2))
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Error making request: {str(e)}")

if __name__ == "__main__":
    main() 