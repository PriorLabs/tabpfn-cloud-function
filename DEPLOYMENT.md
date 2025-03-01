# TabPFN Cloud Function Deployment Guide

This document outlines the steps to deploy the TabPFN Cloud Function to Google Cloud Platform.

## Prerequisites

- Google Cloud CLI (`gcloud`) installed and configured
- Python 3.10 installed
- Git repository cloned

## Deployment Steps

### 1. Project Setup

```bash
# Create a new Google Cloud project (if needed)
gcloud projects create PROJECT_ID --name="PROJECT_NAME"

# Set the active project
gcloud config set project PROJECT_ID

# Enable required APIs
gcloud services enable cloudfunctions.googleapis.com cloudbuild.googleapis.com run.googleapis.com storage.googleapis.com iam.googleapis.com serviceusage.googleapis.com
```

### 2. Configure Environment Variables

Create a `.env.yaml` file with the following variables:

```yaml
# Environment variables for TabPFN Cloud Function
GCS_BUCKET: "your-bucket-name"  # For storing model files if needed
USE_GCS: "false"  # Set to "true" if using Google Cloud Storage for models
USE_MOCK: "true"  # Set to "false" for real TabPFN predictions
TABPFN_API_TOKEN: "your-tabpfn-api-token-here"  # Get this from TabPFN website
```

### 3. Create Storage Buckets (if needed)

```bash
# Create a bucket for model files (if USE_GCS="true")
gsutil mb -l REGION gs://your-bucket-name

# Create a staging bucket for deployment
gsutil mb -l REGION gs://your-function-staging
```

### 4. IAM Permissions

Grant necessary permissions to the Compute service account:

```bash
# Get the project number
PROJECT_NUMBER=$(gcloud projects describe PROJECT_ID --format='value(projectNumber)')

# Grant permissions to Cloud Build service account
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member=serviceAccount:PROJECT_NUMBER@cloudbuild.gserviceaccount.com \
  --role=roles/cloudfunctions.developer

gcloud projects add-iam-policy-binding PROJECT_ID \
  --member=serviceAccount:PROJECT_NUMBER@cloudbuild.gserviceaccount.com \
  --role=roles/cloudbuild.builds.builder
  
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member=serviceAccount:PROJECT_NUMBER@cloudbuild.gserviceaccount.com \
  --role=roles/editor
  
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member=serviceAccount:PROJECT_NUMBER@cloudbuild.gserviceaccount.com \
  --role=roles/storage.admin

# Grant permissions to Compute service account
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member=serviceAccount:PROJECT_NUMBER-compute@developer.gserviceaccount.com \
  --role=roles/storage.objectViewer
```

### 5. Deploy the Function

#### Option 1: Direct Deployment (CLI)

```bash
# Deploy the function
gcloud functions deploy infer-category \
  --gen2 \
  --runtime=python310 \
  --source=. \
  --entry-point=infer_category \
  --trigger-http \
  --allow-unauthenticated \
  --region=REGION \
  --memory=2048MB \
  --timeout=540s \
  --env-vars-file=.env.yaml \
  --project=PROJECT_ID
```

#### Option 2: Deployment via Storage Bucket

```bash
# Create a ZIP file of the source code
zip -r /tmp/function.zip . -x "*.git*" "*.pyc" "__pycache__/*"

# Upload to the staging bucket
gsutil cp /tmp/function.zip gs://your-function-staging/

# Deploy from the staging bucket
gcloud functions deploy infer-category \
  --gen2 \
  --runtime=python310 \
  --source=gs://your-function-staging/function.zip \
  --entry-point=infer_category \
  --trigger-http \
  --allow-unauthenticated \
  --region=REGION \
  --memory=2048MB \
  --timeout=540s \
  --env-vars-file=.env.yaml \
  --project=PROJECT_ID
```

#### Option 3: Google Cloud Console Deployment

1. Visit the Cloud Functions Console: https://console.cloud.google.com/functions/add?env=gen2
2. Configure the function:
   - Name: infer-category
   - Region: your-region
   - Choose to trigger the function via HTTP
   - Set to 2nd gen
   - Authentication: Allow unauthenticated invocations
3. For source code:
   - Connect to your GitHub repository or
   - Upload a ZIP file of your code
4. Runtime settings:
   - Runtime: Python 3.10
   - Entry point: infer_category
   - Memory: 2048 MB
   - Timeout: 540 seconds
5. Environment variables:
   - Add the variables from your .env.yaml file
6. Click "Deploy"

### 6. Test the Deployment

After deployment, you'll get two URLs:

1. Cloud Functions URL: `https://REGION-PROJECT_ID.cloudfunctions.net/infer-category`
2. Cloud Run Service URL: `https://<service-name>-<hash>-<region>.a.run.app`

Either URL should work for invoking your function. When integrating with Google Sheets, you may find that the Cloud Run Service URL is more reliable and has better performance.

### 7. Setting Up Real TabPFN Predictions

By default, the function is deployed in mock mode. To switch to real TabPFN predictions:

1. Use the provided `update_function.py` script:
   ```bash
   python update_function.py --use-mock false
   ```

2. This script will:
   - Log in to TabPFN with your credentials
   - Get an API token
   - Update your function's environment variables
   - Redeploy the configuration

For detailed instructions on using this script, see [UPDATE_TOKEN.md](UPDATE_TOKEN.md). Use the included test script:

```bash
# Make the test script executable
chmod +x test_deployment.py

# Run the test against your deployed function (try both URLs if one doesn't work)
python test_deployment.py --url "https://REGION-PROJECT_ID.cloudfunctions.net/infer-category" --verbose
# Or
python test_deployment.py --url "https://<service-name>-<hash>-<region>.a.run.app" --verbose
```

Or use curl directly:

```bash
curl -X POST "https://<service-name>-<hash>-<region>.a.run.app" \
  -H "Content-Type: application/json" \
  -d '{"transactions": [{"date": "2023-01-01", "description": "GROCERY STORE", "amount": -45.67}]}'
```

## Troubleshooting Common Issues

### Permission Errors

If you encounter permission errors during deployment:

1. Check the Cloud Build logs for specific permission errors
2. Grant additional permissions to the service accounts:
   ```bash
   gcloud projects add-iam-policy-binding PROJECT_ID \
     --member=serviceAccount:SERVICE_ACCOUNT \
     --role=REQUIRED_ROLE
   ```

### Deployment Times Out

For large deployments:

1. Increase the timeout for gcloud commands:
   ```bash
   gcloud config set functions/deployment_time_timeout 30m
   ```

### Function Returns 403 Forbidden

If your deployed function returns 403:

1. Make sure you selected "Allow unauthenticated invocations" during deployment
2. Update the permissions on the Cloud Run service:
   ```bash
   gcloud run services add-iam-policy-binding SERVICE_NAME \
     --member="allUsers" \
     --role="roles/run.invoker" \
     --region=REGION \
     --project=PROJECT_ID
   ```

## Google Sheets Integration

Update the `CLOUD_FUNCTION_URL` in your `Code.gs` file to point to your deployed function:

```javascript
// Use the Cloud Run Service URL (recommended, more stable)
const CLOUD_FUNCTION_URL = 'https://<service-name>-<hash>-<region>.a.run.app';

// Or use the Cloud Functions URL
// const CLOUD_FUNCTION_URL = 'https://REGION-PROJECT_ID.cloudfunctions.net/infer-category';
```

### Setting up Google Sheets

1. Open your Google Sheet
2. Go to Extensions > Apps Script
3. Paste the contents of the `Code.gs` file
4. Update the `CLOUD_FUNCTION_URL` value as shown above
5. Save and reload your sheet
6. You should now see a "Transaction Categories" menu
7. Select your transaction data
8. Click "Transaction Categories" > "Predict Categories"