import os
import csv
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

def display_api_calls(client):
    """Calls various API methods and prints their raw outputs without additional data structuring."""
    print("Calling API endpoints and displaying raw responses...\n")
    try:
        print("\nclient.get_sampling_markets()")
        print(client.get_sampling_markets())
    except Exception as e:
        print(f"Error calling API methods: {str(e)}")

def filter_markets(client):
    """
    Filtert Märkte nach Enddatum oder Stichwort.
    """
    print("Filterkriterium:")
    print("1. Enddatum")
    print("2. Stichwort")
    option = input("Wählen Sie eine Option (1 oder 2): ").strip()

    try:
        sampling_response = client.get_sampling_markets()
        if isinstance(sampling_response, dict) and "data" in sampling_response:
            markets = sampling_response["data"]
        elif isinstance(sampling_response, list):
            markets = sampling_response
        else:
            markets = []
    except Exception as e:
        print(f"Fehler beim Abrufen der Märkte: {str(e)}")
        return

    if option == "1":
        date_filter = input("Bitte geben Sie das Enddatum ein (YYYY-MM-DD): ").strip()
        constructed_date = f"{date_filter}T00:00:00Z"  # Konkateniere mit Zeit
        filtered = [m for m in markets if m.get("end_date_iso") == constructed_date]

        if not filtered:
            print("Keine Märkte mit diesem Enddatum gefunden.")
        else:
            filename = f"{date_filter}.csv"
            with open(filename, "w", newline="", encoding="utf-8") as csvfile:
                csvwriter = csv.writer(csvfile)
                csvwriter.writerow(["event_slug", "link"])
                for m in filtered:
                    event_slug = m.get("market_slug", "N/A")
                    link = f"https://polymarket.com/event/{event_slug}"
                    csvwriter.writerow([event_slug, link])
            print(f"CSV-Datei '{filename}' wurde erstellt.")

    elif option == "2":
        keyword = input("Bitte geben Sie das Stichwort ein: ").strip().lower()
        filtered = [m for m in markets if keyword in m.get("market_slug", "").lower()]
        if not filtered:
            print("Keine Märkte mit diesem Stichwort gefunden.")
        else:
            for m in filtered:
                event_slug = m.get("event_slug", "N/A")
                link = f"https://polymarket.com/event/{event_slug}"
                condition_id = m.get("condition_id", "N/A")
                print(f"Event: {link} | condition_id: {condition_id}")
    else:
        print("Ungültige Auswahl.")

def fetch_info_from_url(client):
    """
    Extrahiert Marktdaten direkt aus der CLOB API unter Verwendung des Event-Links
    durch Kombination von get_markets() und get_sampling_simplified_markets()
    """
    print("\n--- Polymarket Link Analysis ---")
    url = input("Bitte geben Sie den vollständigen Polymarket-Event-Link ein: ").strip()

    try:
        # Schritt 1: Extrahiere Slug aus der URL
        if "polymarket.com/event/" not in url:
            print("Ungültiges URL-Format")
            return

        slug = url.split("/event/")[-1].split("?")[0].split("#")[0]
        print(f"Analysiere Slug: {slug}")

        # Schritt 2: Finde condition_id über get_markets()
        print("Durchsuche Märkte...")
        target_condition_id = None
        next_cursor = ""

        while True:
            markets_response = client.get_markets(next_cursor=next_cursor)
            markets = markets_response.get("data", [])

            for market in markets:
                if market.get("market_slug") == slug or market.get("event_slug") == slug:
                    target_condition_id = market["condition_id"]
                    break

            if target_condition_id or not markets_response.get("next_cursor"):
                break

            next_cursor = markets_response["next_cursor"]

        if not target_condition_id:
            print(f"Kein Markt mit Slug '{slug}' gefunden")
            return

        # Schritt 3: Hole detaillierte Daten von beiden Endpoints
        detailed_market = client.get_market(target_condition_id).get("market", {})
        simplified_markets = client.get_sampling_simplified_markets().get("data", [])
        simplified_data = next((m for m in simplified_markets if m["condition_id"] == target_condition_id), {})

        # Datenkonsolidierung
        market_data = {
            # Basisinformationen
            "condition_id": target_condition_id,
            "slug": slug,
            "question": detailed_market.get("question", "N/A"),
            "category": detailed_market.get("category", "N/A"),
            "end_date": detailed_market.get("end_date_iso", "N/A")[:10],

            # Handelsdaten
            "yes_price": next((t["price"] for t in simplified_data.get("tokens", []) if t["outcome"] == "Yes"), "N/A"),
            "no_price": next((t["price"] for t in simplified_data.get("tokens", []) if t["outcome"] == "No"), "N/A"),

            # Rewards
            "min_size": simplified_data.get("rewards", {}).get("min_size", "N/A"),
            "max_spread": simplified_data.get("rewards", {}).get("max_spread", "N/A"),
            "daily_reward": simplified_data.get("rewards", {}).get("rates", [{}])[0].get("rewards_daily_rate", "N/A"),

            # Status
            "active": simplified_data.get("active", False),
            "closed": simplified_data.get("closed", False),
            "accepting_orders": simplified_data.get("accepting_orders", False)
        }

        # CSV-Export
        filename = f"polymarket_{slug}.csv"
        with open(filename, "w", newline="", encoding="utf-8") as csvfile:
            fieldnames = [
                'condition_id', 'slug', 'question', 'category', 'end_date',
                'yes_price', 'no_price', 'min_size', 'max_spread', 'daily_reward',
                'active', 'closed', 'accepting_orders'
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerow(market_data)

        print(f"\n✅ Erfolgreich gespeichert als: {filename}")
        print("Enthaltene Daten:")
        for key, value in market_data.items():
            print(f"{key:>15}: {value}")

    except Exception as e:
        print(f"\n❌ Fehler: {str(e)}")


def filter_for_info(client):
    """
    """
    condition_id = input("Bitte condition_id eingeben: ").strip()

    try:
        print(client.get_market(condition_id))
    except Exception as e:
        print(f"\n❌ Fehler: {str(e)}")

def fetch_all_market_data(client):
    """Fetches Event, Market End, CONDITION_ID, Token_ID, Outcome, Price for all markets and saves to CSV."""
    try:
        # Fetch market data from the API
        response = client.get_sampling_markets()

        # Handle different possible response formats
        if isinstance(response, dict) and "data" in response:
            markets = response["data"]
        elif isinstance(response, list):
            markets = response
        else:
            markets = []
            print("No market data received from API.")
            return

        # Open CSV file for writing
        with open("all_market_data.csv", "w", newline="", encoding="utf-8") as csvfile:
            csvwriter = csv.writer(csvfile)
            # Write header row
            csvwriter.writerow(["Event", "Market End", "CONDITION_ID", "Token_ID", "Outcome", "Price"])

            # Process each market and its tokens
            for market in markets:
                event = market.get("market_slug", "N/A")
                market_end = market.get("end_date_iso", "N/A")
                condition_id = market.get("condition_id", "N/A")
                tokens = market.get("tokens", [])

                # Write a row for each token in the market
                for token in tokens:
                    token_id = token.get("token_id", "N/A")
                    outcome = token.get("outcome", "N/A")
                    price = token.get("price", "N/A")
                    csvwriter.writerow([event, market_end, condition_id, token_id, outcome, price])

        print("Data successfully saved to the CSV file.'")

    except Exception as e:
        print(f"Error fetching market data: {str(e)}")

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
            print("1. Retrieve Market (Filter: Enddatum / Stichwort)")
            print("2. Fetch info (via Polymarket Link)")
            print("3. Filter (via condition_id)")
            print("4. Call API Methods (Raw Output)")
            print("5. Fetch All Market Data")  # New option added
            print("6. Exit")  # Exit shifted to option 6
            choice = input("Select an option: ").strip()

            if choice == '1':
                filter_markets(client)
            elif choice == '2':
                fetch_info_from_url(client)
            elif choice == '3':
                filter_for_info(client)
            elif choice == '4':
                display_api_calls(client)
            elif choice == '5':
                fetch_all_market_data(client)
            elif choice == '6':
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
