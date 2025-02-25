# TabPFN Cloud Function

This repository contains a Google Cloud Function that runs TabPFN classification models to categorize transactions. It's designed to work with Google Sheets data and provides a simple API for classification tasks.

## Overview

TabPFN Cloud Function is built to:
- Process transaction data from API requests
- Apply machine learning (TabPFN) to classify transactions into categories
- Return predictions via HTTP responses
- Handle authentication and rate limiting
- Support Google Cloud Storage for model storage and retrieval

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

## Testing

Run tests using:
```
python -m test_function.py
```

For local testing without deploying:
```
python -m test_local.py
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgements

- [TabPFN](https://github.com/automl/TabPFN) for the underlying classification technology
- Google Cloud Platform for serverless infrastructure 