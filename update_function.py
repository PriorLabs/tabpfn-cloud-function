#!/usr/bin/env python3
"""
Script to update the TabPFN Cloud Function with a real API token.
This script uses tabpfn_client to log in and retrieve a token,
then updates the function's environment variables.
"""

import argparse
import subprocess
import os
import sys
import json
import logging
import getpass
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_tabpfn_client():
    """Check if tabpfn_client is installed."""
    try:
        import tabpfn_client
        return True
    except ImportError:
        return False

def get_tabpfn_token(email=None, password=None, save_token=True):
    """Get TabPFN API token using tabpfn_client."""
    try:
        from tabpfn_client import get_access_token
        
        # If credentials not provided, prompt for them
        if not email:
            email = input("Enter your TabPFN email: ")
        if not password:
            password = getpass.getpass("Enter your TabPFN password: ")
        
        logger.info(f"Logging in to TabPFN as {email}...")
        token = get_access_token(email, password)
        
        if not token:
            logger.error("❌ Failed to get TabPFN token. Please check your credentials.")
            return None
        
        logger.info("✅ Successfully retrieved TabPFN API token")
        
        # Optionally save token to a local file
        if save_token:
            token_file = Path.home() / ".tabpfn_token"
            with open(token_file, "w") as f:
                f.write(token)
            logger.info(f"Token saved to {token_file}")
            # Set restrictive permissions
            os.chmod(token_file, 0o600)
        
        return token
    except Exception as e:
        logger.error(f"Error getting TabPFN token: {str(e)}")
        return None

def check_gcloud_installed():
    """Check if gcloud CLI is installed and available."""
    try:
        subprocess.run(["gcloud", "--version"], capture_output=True, check=True, text=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def check_auth_status():
    """Check if the user is authenticated with gcloud."""
    try:
        result = subprocess.run(["gcloud", "auth", "list"], capture_output=True, check=True, text=True)
        return "No credentialed accounts." not in result.stdout
    except subprocess.CalledProcessError:
        return False

def get_current_project():
    """Get the current GCP project ID."""
    try:
        result = subprocess.run(["gcloud", "config", "get-value", "project"], 
                                capture_output=True, check=True, text=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return None

def get_function_details(project_id, region, function_name):
    """Get the current details of the deployed function."""
    try:
        result = subprocess.run([
            "gcloud", "functions", "describe", function_name,
            "--region", region,
            "--project", project_id,
            "--format", "json"
        ], capture_output=True, check=True, text=True)
        
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to get function details: {e}")
        logger.error(f"Output: {e.stderr}")
        return None

def update_function_env_vars(project_id, region, function_name, env_vars):
    """Update the environment variables of the deployed function."""
    try:
        # Format env vars for command line
        env_vars_str = ",".join([f"{k}={v}" for k, v in env_vars.items()])
        
        logger.info(f"Updating environment variables for function {function_name}")
        
        # Construct and run the command
        cmd = [
            "gcloud", "functions", "deploy", function_name,
            "--gen2",
            "--region", region,
            "--project", project_id,
            "--update-env-vars", env_vars_str,
            "--quiet"  # Suppress prompts
        ]
        
        logger.info("Running update command...")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info("✅ Function updated successfully")
            return True
        else:
            logger.error(f"Failed to update function: {result.stderr}")
            return False
    except Exception as e:
        logger.error(f"Error updating function: {str(e)}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Update the TabPFN Cloud Function with a real API token")
    parser.add_argument("--project", help="Google Cloud project ID")
    parser.add_argument("--region", default="us-central1", help="GCP region where the function is deployed")
    parser.add_argument("--function", default="infer-category", help="Function name")
    parser.add_argument("--email", help="TabPFN account email")
    parser.add_argument("--password", help="TabPFN account password (not recommended - use prompt)")
    parser.add_argument("--token", help="Use existing TabPFN token (skip login)")
    parser.add_argument("--use-mock", choices=["true", "false"], default="false", 
                      help="Whether to use mock predictions (default: false)")
    parser.add_argument("--use-gcs", choices=["true", "false"], default="false",
                      help="Whether to use GCS for storage (default: false)")
    parser.add_argument("--no-save-token", action="store_true", help="Don't save token to ~/.tabpfn_token")
    
    args = parser.parse_args()
    
    # Check gcloud installation
    if not check_gcloud_installed():
        logger.error("❌ gcloud CLI not found. Please install the Google Cloud SDK.")
        return 1
    
    # Check authentication
    if not check_auth_status():
        logger.error("❌ Not authenticated with gcloud. Please run 'gcloud auth login'.")
        return 1
    
    # Check tabpfn_client installation
    if not check_tabpfn_client() and not args.token:
        logger.error("❌ tabpfn_client not found. Please install it with: pip install tabpfn-client")
        return 1
    
    # Get project ID
    project_id = args.project or get_current_project()
    if not project_id:
        logger.error("❌ Could not determine project ID. Please specify with --project.")
        return 1
    
    logger.info(f"Using project: {project_id}")
    logger.info(f"Region: {args.region}")
    logger.info(f"Function: {args.function}")
    
    # Get TabPFN API token
    api_token = args.token
    if not api_token:
        # Check for saved token
        token_file = Path.home() / ".tabpfn_token"
        if token_file.exists() and not args.email:
            with open(token_file, "r") as f:
                api_token = f.read().strip()
            logger.info(f"Using saved token from {token_file}")
        else:
            api_token = get_tabpfn_token(args.email, args.password, not args.no_save_token)
    
    if not api_token:
        logger.error("❌ Could not get TabPFN API token. Exiting.")
        return 1
    
    # Get function details
    function_details = get_function_details(project_id, args.region, args.function)
    if not function_details:
        logger.error(f"❌ Could not retrieve details for function {args.function}")
        return 1
    
    # Get current environment variables
    current_env_vars = {}
    if "serviceConfig" in function_details and "environmentVariables" in function_details["serviceConfig"]:
        current_env_vars = function_details["serviceConfig"]["environmentVariables"]
    
    logger.info("Current environment variables:")
    for k, v in current_env_vars.items():
        if k == "TABPFN_API_TOKEN":
            logger.info(f"  {k}: ********")
        else:
            logger.info(f"  {k}: {v}")
    
    # Update environment variables
    new_env_vars = current_env_vars.copy()
    new_env_vars["TABPFN_API_TOKEN"] = api_token
    new_env_vars["USE_MOCK"] = args.use_mock
    new_env_vars["USE_GCS"] = args.use_gcs
    
    logger.info("New environment variables:")
    for k, v in new_env_vars.items():
        if k == "TABPFN_API_TOKEN":
            logger.info(f"  {k}: ********")
        else:
            logger.info(f"  {k}: {v}")
    
    # Confirm before proceeding
    if input("Continue with update? (y/n): ").lower() != "y":
        logger.info("Update cancelled.")
        return 0
    
    # Update the function
    success = update_function_env_vars(project_id, args.region, args.function, new_env_vars)
    
    if success:
        logger.info("✅ Function updated successfully with the new API token")
        logger.info(f"Mode: {'Mock' if args.use_mock == 'true' else 'Real TabPFN API'}")
        
        # Get the URLs
        service_uri = function_details.get("serviceConfig", {}).get("uri", "")
        function_url = function_details.get("url", "")
        
        if service_uri:
            logger.info(f"Cloud Run URL: {service_uri}")
        if function_url:
            logger.info(f"Function URL: {function_url}")
            
        return 0
    else:
        logger.error("❌ Failed to update function")
        return 1

if __name__ == "__main__":
    sys.exit(main())