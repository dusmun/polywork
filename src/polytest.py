import os
import json
from dotenv import load_dotenv
from py_clob_client.client import ClobClient
from py_clob_client.clob_types import ApiCreds
from py_clob_client.constants import AMOY

def display_header():
    """Displays the ASCII art header for PolyBot."""
    print(r"""
 ____  _____  __    _  _  ____  _____  ____ 
(  _ \(  _  )(  )  ( \/ )(  _ \(  _  )(_  _)
 )___/ )(_)(  )(__  \  /  ) _ < )(_)(   )(  
(__)  (_____)(____) (__) (____/(_____) (__)               
""")

def retrieve_markets(client):
    """Retrieves and displays active markets from the Polymarket CLOB API in a structured way."""
    print("Fetching structured market data...")
    try:
        response = client.get_simplified_markets()

        # Debug: Check response type
        if isinstance(response, str):
            markets = json.loads(response)
        else:
            markets = response

        if not isinstance(markets, list):
            print("Unexpected response format from API")
            return

        active_markets = []
        for market in markets:
            if isinstance(market, dict) and market.get('active', False):
                active_markets.append(market)

        print(f"Found {len(active_markets)} active markets.")
        print(f"{'Question':<50} {'Slug':<30} {'End Date':<10} {'Yes Price':<10} {'No Price':<10}")

        for market in active_markets:
            try:
                question = market.get('question', 'N/A')
                question = question[:47] + '...' if len(question) > 50 else question

                slug = market.get('market_slug', 'N/A')
                slug = slug[:27] + '...' if len(slug) > 30 else slug

                end_date = market.get('end_date_iso', 'N/A')[:10]

                prices = {'Yes': None, 'No': None}
                for token in market.get('tokens', []):
                    outcome = token.get('outcome')
                    if outcome in prices:
                        prices[outcome] = token.get('price')

                yes_price = f"{prices['Yes']:.4f}" if prices['Yes'] is not None else 'N/A'
                no_price = f"{prices['No']:.4f}" if prices['No'] is not None else 'N/A'
                print(f"{question:<50} {slug:<30} {end_date:<10} {yes_price:<10} {no_price:<10}")

            except Exception as market_error:
                print(f"Error processing market: {str(market_error)}")
                continue

    except json.JSONDecodeError:
        print("Failed to parse API response")
    except Exception as e:
        print(f"API request failed: {str(e)}")

def display_api_calls(client):
    """Calls various API methods and prints their raw outputs without additional data structuring."""
    print("Calling API endpoints and displaying raw responses...\n")
    try:
        # print("\nclient.get_simplified_markets()") # Einfach nur Rates und Conditions / Price
        # print(client.get_simplified_markets())

        # Das sind die actual markets
        print("\nclient.get_sampling_markets()")
        print(client.get_sampling_markets())


        # print("\nclient.get_market('condition_id')")
        # print(client.get_market("0x2252e40afd74bdcd5a7ed98e7e71e102b19b74513bd763dee870fc779f87c775"))
    except Exception as e:
        print(f"Error calling API methods: {str(e)}")

def main():
    """Main function to run the PolyBot CLI."""
    try:
        load_dotenv()

        # Verify environment variables
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

        # Initialize client using the environment variables
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
            print("1. Retrieve Structured Markets")
            print("2. Call API Methods (Raw Output)")
            print("3. Exit")
            choice = input("Select an option: ").strip()

            if choice == '1':
                retrieve_markets(client)
            elif choice == '2':
                display_api_calls(client)
            elif choice == '3':
                print("Exiting...")
                break
            else:
                print("Invalid option. Please try again.")

    except ValueError as ve:
        print(f"Configuration error: {str(ve)}")
    except Exception as e:
        print(f"Critical error: {str(e)}")

if __name__ == "__main__":
    main()
