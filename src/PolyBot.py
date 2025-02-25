import os
import json
import csv
from dotenv import load_dotenv
from py_clob_client.client import ClobClient
from py_clob_client.clob_types import ApiCreds
from py_clob_client.constants import AMOY

def display_header():
    """Displays the ASCII art header."""
    print(r"""
 ____  _____  __    _  _  ____  _____  ____ 
(  _ \(  _  )(  )  ( \/ )(  _ \(  _  )(_  _)
 )___/ )(_)(  )(__  \  /  ) _ < )(_)(   )(  
(__)  (_____)(____) (__) (____/(_____) (__)               
""")

def retrieve_market(client):
    """
    Retrieves market data using client.get_sampling_markets(), extracts:
      - market_slug
      - end_date_iso
      - for each token: token_id, outcome, price
    and writes the data into a CSV file named 'Market_data.csv'.
    """
    print("Fetching market data using get_sampling_markets() ...")
    try:
        # Retrieve the data from the API
        response = client.get_sampling_markets()

        # If response is a JSON string, convert it to a Python object.
        if isinstance(response, str):
            try:
                response = json.loads(response)
            except json.JSONDecodeError as jde:
                print("Failed to parse API response as JSON:", jde)
                return

        # Process response to extract a list of markets.
        markets = []
        if isinstance(response, list):
            markets = response
        elif isinstance(response, dict):
            # Check for common keys that may hold the list of markets
            if "markets" in response and isinstance(response["markets"], list):
                markets = response["markets"]
            elif "data" in response and isinstance(response["data"], list):
                markets = response["data"]
            else:
                # If the dict doesn't hold a list, wrap it in a list.
                markets = [response]
        else:
            print("Unexpected response format from API")
            return

        # Prepare CSV file for writing
        csv_file = "market_data.csv"
        with open(csv_file, mode="w", newline="") as file:
            writer = csv.writer(file)
            # Write header row
            writer.writerow(["Event", "Market End", "CONDITION_ID", "Token_ID", "Outcome", "Price"])

            # Loop through each market and extract the needed data.
            for market in markets:
                market_slug = market.get("market_slug", "N/A")
                condition_id = market.get("condition_id", "N/A")
                end_date = market.get("end_date_iso", "N/A")
                tokens = market.get("tokens", [])
                # Write one row per token in this market
                for token in tokens:
                    token_id = token.get("token_id", "N/A")
                    outcome = token.get("outcome", "N/A")
                    price = token.get("price", "N/A")
                    writer.writerow([market_slug, end_date, condition_id, token_id, outcome, price])

        print(f"Market data successfully written to '{csv_file}'.")
    except Exception as e:
        print(f"API request failed: {str(e)}")

def main():
    """Main function to run the CLI."""
    try:
        load_dotenv()

        # Verify required environment variables
        required_vars = [
            "POLYMARKET_HOST",
            "POLYMARKET_KEY",
            "POLYMARKET_API_KEY",
            "POLYMARKET_API_SECRET",
            "POLYMARKET_API_PASSPHRASE"
        ]
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        if missing_vars:
            raise ValueError(f"Missing environment variables: {', '.join(missing_vars)}")

        # Initialize client
        client = ClobClient(
            host=os.getenv("POLYMARKET_HOST"),
            key=os.getenv("POLYMARKET_KEY"),
            chain_id=AMOY,
            creds=ApiCreds(
                api_key=os.getenv("POLYMARKET_API_KEY"),
                api_secret=os.getenv("POLYMARKET_API_SECRET"),
                api_passphrase=os.getenv("POLYMARKET_API_PASSPHRASE")
            )
        )

        display_header()

        while True:
            print("\nOptions:")
            print("1. Retrieve Market")
            print("2. Exit")
            print("3. Testing")
            choice = input("Select an option: ").strip()

            if choice == '1':
                retrieve_market(client)
            elif choice == '2':
                print("Exiting...")
                break
            elif choice == '3':
                response = client.get_sampling_markets()
                print("Response type:", type(response))
                # not needed rn
                # print("Response content:", response)
            else:
                print("Invalid option. Please try again.")

    except ValueError as ve:
        print(f"Configuration error: {str(ve)}")
    except Exception as e:
        print(f"Critical error: {str(e)}")

if __name__ == "__main__":
    main()
