# Updating Your TabPFN Cloud Function Token

This document explains how to use the `update_function.py` script to update your deployed cloud function with a new TabPFN API token and switch from mock mode to real predictions.

## Prerequisites

- Python 3.6 or higher
- `tabpfn-client` package installed (`pip install tabpfn-client`)
- Google Cloud SDK installed and configured
- A TabPFN account (sign up at [tabpfn.github.io](https://tabpfn.github.io) if needed)

## Usage

The script provides several options for updating your function:

### 1. Basic Usage (Interactive)

Simply run the script with no arguments to be prompted for all necessary information:

```bash
python update_function.py
```

This will:
- Detect your current GCP project
- Prompt for your TabPFN email and password
- Retrieve an API token
- Save the token to `~/.tabpfn_token` for future use
- Update your cloud function to use the real TabPFN API

### 2. Provide TabPFN Credentials

```bash
python update_function.py --email your.email@example.com
```

You'll be prompted securely for your password.

### 3. Use an Existing Token

If you already have a TabPFN API token:

```bash
python update_function.py --token "your-api-token"
```

### 4. Specify GCP Project and Region

```bash
python update_function.py --project your-project-id --region us-central1
```

### 5. Keep Using Mock Mode (but with a Valid Token)

```bash
python update_function.py --use-mock true
```

## Full Options Reference

```
usage: update_function.py [-h] [--project PROJECT] [--region REGION]
                         [--function FUNCTION] [--email EMAIL]
                         [--password PASSWORD] [--token TOKEN]
                         [--use-mock {true,false}] [--use-gcs {true,false}]
                         [--no-save-token]

options:
  -h, --help            show this help message and exit
  --project PROJECT     Google Cloud project ID
  --region REGION       GCP region where the function is deployed
  --function FUNCTION   Function name
  --email EMAIL         TabPFN account email
  --password PASSWORD   TabPFN account password (not recommended - use prompt)
  --token TOKEN         Use existing TabPFN token (skip login)
  --use-mock {true,false}
                        Whether to use mock predictions (default: false)
  --use-gcs {true,false}
                        Whether to use GCS for storage (default: false)
  --no-save-token       Don't save token to ~/.tabpfn_token
```

## How It Works

1. The script logs in to TabPFN using your credentials and obtains an API token
2. It retrieves the current configuration of your deployed cloud function
3. It updates the environment variables with the new token and settings
4. It redeploys only the configuration (not the entire function)

## Troubleshooting

If you encounter issues:

1. **Authentication errors**: Make sure you're using the correct TabPFN credentials
2. **Permission errors**: Ensure your Google Cloud account has permission to update the function
3. **Token not working**: Try logging in to the TabPFN website to verify your account status
4. **Cloud Function not found**: Check the function name and region with `gcloud functions list`

## Security Notes

- The script stores your TabPFN token in `~/.tabpfn_token` with restricted permissions (readable only by you)
- Never include your TabPFN password in command line arguments (use the prompt)
- The token is securely transmitted to Google Cloud and stored as an environment variable

## Testing After Update

After updating your function, you can test it with the test_deployment.py script:

```bash
python test_deployment.py --url "https://your-function-url" --verbose
```