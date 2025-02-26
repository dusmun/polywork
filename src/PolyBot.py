import os
import json
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

def retrieve_markets(client):
    """Retrieves and displays active markets from the Polymarket CLOB API in a structured way."""
    print("Fetching structured market data...")
    try:
        response = client.get_simplified_markets()
        # Falls die API einen JSON-String zurückgibt
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
    Neue Funktion 2: Ermöglicht das Einfügen eines Polymarket-Links.
      - Extrahiert den event_slug aus der URL.
      - Sucht den entsprechenden Markt.
      - Ruft über die condition_id den vollständigen Markt ab.
      - Schreibt ausgewählte Informationen in eine CSV-Datei (Dateiname = event_slug.csv).
    """
    url = input("Paste URL: ").strip()
    if "polymarket.com/event/" not in url:
        print("Ungültige URL.")
        return
    try:
        event_slug = url.split("/event/")[1]
    except IndexError:
        print("Fehler beim Extrahieren des event_slug.")
        return

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

    matched_market = None
    for m in markets:
        if m.get("event_slug", "").lower() == event_slug.lower():
            matched_market = m
            break

    if not matched_market:
        print("Kein Markt mit diesem event_slug gefunden.")
        return

    condition_id = matched_market.get("condition_id")
    try:
        full_market = client.get_market(condition_id)
    except Exception as e:
        print(f"Fehler beim Abrufen des Marktes: {str(e)}")
        return

    filename = f"{event_slug}.csv"
    with open(filename, "w", newline="", encoding="utf-8") as csvfile:
        csvwriter = csv.writer(csvfile)
        # Hier werden nur die wichtigsten Infos abgespeichert; passe die Spalten nach Bedarf an
        csvwriter.writerow(["condition_id", "question", "description", "market_slug", "end_date_iso"])
        row = [
            full_market.get("condition_id", "N/A"),
            full_market.get("question", "N/A"),
            full_market.get("description", "N/A"),
            full_market.get("market_slug", "N/A"),
            full_market.get("end_date_iso", "N/A")[:10] if full_market.get("end_date_iso") else "N/A"
        ]
        csvwriter.writerow(row)
    print(f"Markt-Infos wurden in '{filename}' gespeichert.")

def generate_link_from_condition(client):
    """
    Generiert einen Polymarket-Link basierend auf einer condition_id.
    Verwendet client.get_sampling_markets(), um die Daten zu holen.
    """
    condition_id = input("Bitte condition_id eingeben: ").strip()
    try:
        sampling_response = client.get_sampling_markets()
        # Verarbeite die API-Response
        if isinstance(sampling_response, dict) and "data" in sampling_response:
            markets = sampling_response["data"]
        elif isinstance(sampling_response, list):
            markets = sampling_response
        else:
            markets = []
    except Exception as e:
        print(f"Fehler beim Abrufen der Märkte: {str(e)}")
        return

    # Suche den Markt mit der condition_id
    found_market = next((m for m in markets if m.get("condition_id") == condition_id), None)
    if not found_market:
        print(f"Kein Markt mit der condition_id '{condition_id}' gefunden.")
        return

    event_slug = found_market.get("event_slug")
    if not event_slug:
        print("event_slug nicht gefunden.")
        return

    link = f"https://polymarket.com/event/{event_slug}"
    print(f"Generierter Link: {link}")

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
            print("3. Link Generator (via condition_id)")
            print("4. Retrieve Structured Markets (Standard)")
            print("5. Call API Methods (Raw Output)")
            print("6. Exit")
            choice = input("Select an option: ").strip()

            if choice == '1':
                filter_markets(client)
            elif choice == '2':
                fetch_info_from_url(client)
            elif choice == '3':
                generate_link_from_condition(client)
            elif choice == '4':
                retrieve_markets(client)
            elif choice == '5':
                display_api_calls(client)
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
