from tabpfn_client import init, get_access_token
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    # Initialize TabPFN client which will handle interactive login if needed
    init()
    
    # Get the token after authentication
    token = get_access_token()
    logger.info("Successfully authenticated with TabPFN")
    logger.info(f"Token: {token}")
    
    # Save token to .env.yaml
    with open('.env.yaml', 'w') as f:
        f.write(f"""GCS_BUCKET: "your_bucket_name"
USE_GCS: "true"
USE_MOCK: "false"
TABPFN_API_TOKEN: "{token}"
""")
    logger.info("Token saved to .env.yaml")

if __name__ == "__main__":
    main() 