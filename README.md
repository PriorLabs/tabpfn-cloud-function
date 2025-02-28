# TabPFN Cloud Function

This repository contains a Google Cloud Function that runs TabPFN classification models to categorize transactions. It's designed to work with Google Sheets data and provides a simple API for classification tasks.

> **Note**: This is a fork of [belalanne/tabpfn-cloud-function](https://github.com/belalanne/tabpfn-cloud-function). All credit for the original implementation goes to the original author.


https://github.com/user-attachments/assets/811e2d33-9e8b-4b42-85ea-90bb27cc3cfe


## Overview

TabPFN Cloud Function is built to:
- Process transaction data from API requests
- Apply machine learning (TabPFN) to classify transactions into categories
- Return predictions via HTTP responses
- Handle authentication and rate limiting
- Support Google Cloud Storage for model storage and retrieval

## Project Structure

### Architecture Flow

```
┌─────────────────┐     ┌───────────────┐     ┌───────────────────┐     ┌───────────────┐
│  Google Sheets  │────▶│  Apps Script  │────▶│  Cloud Function   │────▶│  Cloud Storage│
└─────────────────┘     └───────────────┘     └───────────────────┘     └───────────────┘
                                                        │
                                                        ▼
                                               ┌───────────────────┐
                                               │   TabPFN Client   │
                                               └───────────────────┘
```

### Directory Structure

```
cloud_function@google_apps_script/
├── .env.example.yaml          # Example environment configuration
├── .env.prod                  # Production environment variables
├── .env.test                  # Test environment variables
├── .env.yaml                  # Current environment configuration
├── .gcloudignore              # Files to exclude from deployment
├── .gitattributes             # Git attributes configuration
├── .gitignore                 # Git ignore file
├── Code.gs                    # Google Apps Script integration
├── README.md                  # This documentation
├── cloudbuild.example.yaml    # Example Cloud Build configuration
├── cloudbuild.yaml            # Cloud Build configuration
├── deploy.ps1                 # PowerShell deployment script
├── get_token.py               # API token management utility
├── main.py                    # Main Cloud Function entrypoint
├── predictor.py               # Transaction prediction logic
├── preprocessing.py           # Data preprocessing utilities
├── requirements.txt           # Python dependencies
├── models/                    # Model files directory
│   ├── .gitkeep               # Placeholder for git
│   └── tabpfn-client/         # TabPFN model directory
│       ├── .gitkeep           # Placeholder for git
│       ├── tabpfn_model.pkl   # Main TabPFN model
│       └── transformers.pkl   # Model transformers
```

### Component Descriptions

1. **Google Sheets**: End-user interface where transactions are stored and categorized
2. **Apps Script (Code.gs)**: Google Apps Script that creates a custom menu and handles communication with the Cloud Function
3. **Cloud Function (main.py)**: HTTP endpoint that receives transaction data and returns predictions
4. **Cloud Storage**: Stores TabPFN model files for the Cloud Function to access
5. **TabPFN Client (predictor.py)**: Core ML component that categorizes transactions using the TabPFN model

## Requirements

- Python 3.10
- Google Cloud Platform account
- TabPFN API token (from [TabPFN](https://tabpfn.github.io/))
- Google Cloud Storage bucket (for model storage)

## Installation

### Local Development

1. Clone this repository:
   ```
   git clone https://github.com/belalanne/tabpfn-cloud-function.git
   cd tabpfn-cloud-function
   ```

2. Create and activate a virtual environment:
   ```
   python -m venv venv
   venv\Scripts\activate  # Windows
   source venv/bin/activate  # Linux/Mac
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Set up environment variables by creating a `.env` file:
   ```
   USE_GCS=false
   USE_MOCK=true
   TABPFN_API_TOKEN=your_api_token_here
   GCS_BUCKET=your_gcs_bucket_name
   ```

### Deployment to Google Cloud Functions

1. Create a GCP project and enable required APIs:
   - Cloud Functions API
   - Cloud Build API
   - Cloud Storage API

2. Set up environment variables:
   - Create a `.env.yaml` file based on the provided template
   - Replace the placeholder values with your actual settings

3. Deploy using gcloud:
   ```
   gcloud functions deploy infer-category \
     --gen2 \
     --region=your-region \
     --runtime=python310 \
     --source=. \
     --entry-point=infer_category \
     --trigger-http \
     --memory=2048MB \
     --timeout=540s \
     --env-vars-file=.env.yaml
   ```

4. Or use the provided deployment script:
   ```
   ./deploy.ps1
   ```

## Usage

### API Endpoint

Once deployed, your function will be available at:
```
https://your-region-your-project.cloudfunctions.net/infer-category
```

### Request Format

Send a POST request with the following JSON structure:
```json
{
  "transactions": [
    {
      "date": "2023-04-15",
      "description": "PAYMENT *GROCERY STORE",
      "amount": -45.67,
      "account": "Checking"
    },
    {
      "date": "2023-04-16",
      "description": "DIRECT DEPOSIT SALARY",
      "amount": 1200.00,
      "account": "Savings"
    }
  ]
}
```

### Response Format

The function returns:
```json
{
  "success": true,
  "results": [
    {
      "date": "2023-04-15",
      "description": "PAYMENT *GROCERY STORE",
      "amount": -45.67,
      "account": "Checking",
      "category": "Groceries",
      "confidence": 0.89
    },
    {
      "date": "2023-04-16",
      "description": "DIRECT DEPOSIT SALARY",
      "amount": 1200.00,
      "account": "Savings",
      "category": "Income",
      "confidence": 0.95
    }
  ],
  "request_id": "20230415_123456_789",
  "mode": "tabpfn"
}
```

## Google Sheets Integration

This function integrates seamlessly with Google Sheets through the provided Apps Script. A comprehensive implementation is available in the `Code.gs` file included in this repository.

### Setting Up Google Sheets Integration

1. In your Google Sheet, go to Extensions > Apps Script
2. Create a new script project
3. Copy the contents of the `Code.gs` file from this repository into your script editor
4. Update the `CLOUD_FUNCTION_URL` variable at the top of the script with your deployed function URL:
   ```javascript
   const CLOUD_FUNCTION_URL = 'https://your-region-your-project.cloudfunctions.net/infer-category';
   ```
5. Save the script and reload your Google Sheet

### Using the Google Sheets Integration

Once set up, the script provides:

- A new "Transaction Categories" menu in your Google Sheet
- Automatic detection of transaction columns
- Batch processing to handle large transaction sets
- Color-coded confidence scores 
- Error handling and reporting
- API usage monitoring

To use:
1. Create a sheet with columns for `dateOp`, `transaction_description`, and `amount`
2. Add your transaction data
3. Select "Transaction Categories" > "Predict Categories" from the menu
4. View the results in the automatically created columns

### Advanced Features

The Google Sheets integration includes:
- Batch processing for large datasets
- API usage tracking and limits display
- Detailed error reporting
- Conditional formatting for confidence scores
- JSON response viewing for debugging

## Model Files Deployment

The TabPFN Cloud Function relies on model files that need to be accessible to the function at runtime. There are two approaches:

### 1. Using Google Cloud Storage (Recommended for Production)

1. Create a Google Cloud Storage bucket:
   ```bash
   gsutil mb -l LOCATION gs://YOUR_BUCKET_NAME
   ```

2. Upload the TabPFN model files to your bucket:
   ```bash
   gsutil cp models/tabpfn-client/*.pkl gs://YOUR_BUCKET_NAME/models/tabpfn-client/
   ```

3. Configure your `.env.yaml` to use GCS:
   ```yaml
   GCS_BUCKET: "your-bucket-name"
   USE_GCS: "true"
   ```

4. Make sure your Cloud Function has permission to access the GCS bucket (using appropriate IAM roles)

### 2. Including Models in Function Deployment (Simpler for Testing)

For smaller models or testing purposes, you can include the model files directly in your deployment:

1. Place the model files in the `models/tabpfn-client/` directory
2. Configure your `.env.yaml` to not use GCS:
   ```yaml
   USE_GCS: "false"
   ```
3. Deploy your function normally

Note: This approach can increase cold start times and may not be suitable for large models.

## Environment Variables

Configure these environment variables for deployment:

| Variable | Description | Example |
|----------|-------------|---------|
| `GCS_BUCKET` | Google Cloud Storage bucket name | `my-models-bucket` |
| `USE_GCS` | Whether to use GCS for model storage | `true` or `false` |
| `USE_MOCK` | Use mock predictions for testing | `true` or `false` |
| `TABPFN_API_TOKEN` | API token for TabPFN | `your_api_token` |

## Developer Workflow

This section covers the recommended workflow for quick development and testing.

### Local Development 

For the fastest iteration cycle:

1. Set up your local environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. Create a local `.env` file with testing settings:
   ```
   USE_GCS=false
   USE_MOCK=true
   TABPFN_API_TOKEN=your_api_token_here
   ```

3. Run the local test server:
   ```bash
   python test_locally.py
   ```

4. Visit http://localhost:8080/send_test in your browser to test the function with sample data

5. For real-time code changes, run the function with automatic reloading:
   ```bash
   python -m functions_framework --target infer_category --debug
   ```

### Test-Driven Development

Use the included test suite for reliable development:

1. Run all tests:
   ```bash
   python -m unittest discover tests
   ```

2. Run a specific test:
   ```bash
   python -m unittest tests.test_predictor.TestPredictor.test_mock_predict
   ```

3. Add tests for new features before implementing them

### Deploy and Test in Cloud

After local testing, deploy to GCP:

1. Edit `.env.yaml` with your production settings
2. Run the deployment script:
   ```bash
   ./deploy.ps1  # On PowerShell
   ```

3. Test the deployed function with the generated test payload:
   ```bash
   curl -X POST [FUNCTION_URL] -H 'Content-Type: application/json' -d @test_payload.json
   ```

### Google Sheets Integration

For testing with Google Sheets:

1. Create a new Google Sheet
2. Open Extensions > Apps Script
3. Paste the contents of `Code.gs` into the script editor
4. Update the `CLOUD_FUNCTION_URL` to your deployed function URL
5. Save and run the script
6. Create a sheet with columns for `dateOp`, `transaction_description`, and `amount`
7. Add sample transaction data
8. Use the new "Transaction Categories" menu to test predictions


## Acknowledgements

- [TabPFN](https://github.com/automl/TabPFN) for the underlying classification technology
- Google Cloud Platform for serverless infrastructure
