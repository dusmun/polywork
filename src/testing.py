from dotenv import load_dotenv
import os
from py_clob_client.client import ClobClient
from py_clob_client.clob_types import ApiCreds

# Load environment variables from .env file
load_dotenv()

client = ClobClient(
    host=os.getenv("POLYMARKET_HOST"),
    key=os.getenv("POLYMARKET_KEY"),
    chain_id=137,
    creds=ApiCreds(
        api_key=os.getenv("POLYMARKET_API_KEY"),
        api_secret=os.getenv("POLYMARKET_API_SECRET"),
        api_passphrase=os.getenv("POLYMARKET_API_PASSPHRASE")
    ),
    signature_type=2,
    funder=os.getenv("POLYMARKET_PROXY_ADDRESS")
)

try:
    # Test API connection
    markets = client.get_sampling_markets()
    print("API-Verbindung erfolgreich")
except Exception as e:
    print(f"API-Verbindungsfehler: {str(e)}")
