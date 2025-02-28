#!/usr/bin/env python3
import os
os.environ.setdefault('TERM', 'xterm-256color')
import csv
import sys
from datetime import datetime
from dotenv import load_dotenv
from py_clob_client.client import ClobClient
from py_clob_client.clob_types import ApiCreds
from py_clob_client.constants import AMOY

def clear_screen():
    """Clears the terminal screen."""
    os.system('cls' if os.name == 'nt' else 'clear')

def display_header():
    """Displays the ASCII art header for PolyBot."""
    header = r"""
 _______  _______  ___      __   __  _______  _______  _______ 
|       ||       ||   |    |  | |  ||  _    ||       ||       |
|    _  ||   _   ||   |    |  |_|  || |_|   ||   _   ||_     _|
|   |_| ||  | |  ||   |    |       ||       ||  | |  |  |   |  
|    ___||  |_|  ||   |___ |_     _||  _   | |  |_|  |  |   |  
|   |    |       ||       |  |   |  | |_|   ||       |  |   |  
|___|    |_______||_______|  |___|  |_______||_______|  |___|                
"""
    print(header)

def pause():
    """Pauses the execution until the user presses Enter."""
    input("\nEnter für Hauptmenü drücken...")

def format_number(value: str) -> str:
    """Formats numeric strings with thousands separators."""
    try:
        num = float(value)
        return f"{num:,.2f}"
    except ValueError:
        return value

def display_orderbook_table(orders: list, order_type: str) -> None:
    """Displays bids/asks in a formatted table."""
    print(f"\n{' ' * 16}{order_type.upper()} ORDERS")
    print(f"{'Preis':<12} | {'Menge':<14} | {'Liquidität':<14}")
    print("-" * 45)
    for order in orders[:10]:  # Show top 10 orders
        price = format_number(order.price)
        size = format_number(order.size)
        liquidity = float(order.price) * float(order.size)
        print(f"{price:<12} | {size:<14} | {format_number(str(liquidity)):<14}")

def retrieve_orderbook(client):
    """Displays detailed orderbook analysis with market depth visualization."""
    clear_screen()
    display_header()

    try:
        token_id = input("Bitte tokenID eingeben: ").strip()
        orderbook = client.get_order_book(token_id)

        # Metadata Section
        print(f"\n{' MARKET ANALYSIS ':=^50}")
        print(f"Asset ID: {orderbook.asset_id}")
        print(f"Timestamp: {datetime.fromtimestamp(int(orderbook.timestamp)/1000):%Y-%m-%d %H:%M:%S}")
        print(f"Market Hash: {orderbook.hash[:12]}...{orderbook.hash[-12:]}\n")

        # Process orders
        sorted_bids = sorted(orderbook.bids, key=lambda x: float(x.price), reverse=True)
        sorted_asks = sorted(orderbook.asks, key=lambda x: float(x.price))

        # Best Prices Section
        best_bid = float(sorted_bids[0].price) if sorted_bids else 0
        best_ask = float(sorted_asks[0].price) if sorted_asks else 0
        spread = best_ask - best_bid if best_bid and best_ask else 0

        print(f"{' Best Bid ':-^23} | {' Best Ask ':-^23} | {' Spread ':-^15}")
        print(f"{best_bid:^20.4f} | {best_ask:^20.4f} | {spread:^13.4f}")

        # Orderbook Visualization
        display_orderbook_table(sorted_bids, "Bid")
        display_orderbook_table(sorted_asks, "Ask")

        # Liquidity Analysis
        total_bid_liquidity = sum(float(b.price) * float(b.size) for b in sorted_bids)
        total_ask_liquidity = sum(float(a.price) * float(a.size) for a in sorted_asks)
        print(f"\n{' LIQUIDITY ':=^50}")
        print(f"Total Bid Liquidity: {format_number(str(total_bid_liquidity))} ETH")
        print(f"Total Ask Liquidity: {format_number(str(total_ask_liquidity))} ETH")

    except Exception as e:
        print(f"\nError: {str(e)}")
    pause()

def display_api_calls(client):
    """Calls various API methods and prints their raw outputs."""
    print("Rufe API-Endpunkte auf und zeige rohe Antworten an...\n")
    try:
        print("\nclient.get_sampling_markets():")
        print(client.get_sampling_markets())
    except Exception as e:
        print(f"Fehler beim Aufruf der API: {str(e)}")
    pause()

def filter_markets(client):
    """Filters markets by end date or keyword."""
    clear_screen()
    display_header()
    print("Filterkriterien:")
    print("1. Enddatum")
    print("2. Stichwort")
    option = input("Wählen Sie eine Option (1 oder 2): ").strip()

    try:
        sampling_response = client.get_sampling_markets()
        markets = sampling_response.get("data", []) if isinstance(sampling_response, dict) else sampling_response
    except Exception as e:
        print(f"Fehler beim Abrufen der Märkte: {str(e)}")
        pause()
        return

    if option == "1":
        date_filter = input("Bitte geben Sie das Enddatum ein (YYYY-MM-DD): ").strip()
        date_filter = datetime.strptime(date_filter, "%Y-%m-%d").date()

        filtered = []

        for m in markets:
            date = m.get("end_date_iso")
            if date:
                date = datetime.strptime(date[:10], "%Y-%m-%d").date()
                if date_filter >= date >= datetime.now().date():
                    filtered.append(m)

        if not filtered:
            print("Keine Märkte mit diesem Enddatum gefunden.")
        else:
            filename = f"{date_filter}.csv"
            try:
                with open(filename, "w", newline="", encoding="utf-8") as csvfile:
                    csvwriter = csv.writer(csvfile)
                    csvwriter.writerow(["event_slug", "link"])
                    for m in filtered:
                        event_slug = m.get("market_slug", "N/A")
                        link = f"https://polymarket.com/event/{event_slug}"
                        csvwriter.writerow([event_slug, link])
                print(f"CSV-Datei '{filename}' wurde erfolgreich erstellt.")
            except Exception as e:
                print(f"Fehler beim Schreiben der CSV-Datei: {str(e)}")
    elif option == "2":
        keyword = input("Stichwort (Filter): ").strip().lower()
        filtered = [m for m in markets if keyword in m.get("market_slug", "").lower()]
        if not filtered:
            print("Keine Märkte mit diesem Stichwort gefunden.")
        else:
            for m in filtered:
                market_slug = m.get("market_slug", "N/A")
                condition_id = m.get("condition_id", "N/A")
                print(f"Event: {market_slug} | condition_id: {condition_id}")
    else:
        print("Ungültige Auswahl.")
    pause()

def fetch_info_from_url(client):
    """Extracts market data from Polymarket event link."""
    clear_screen()
    display_header()
    print("--- Polymarket Link Analyse ---")
    url = input("Bitte geben Sie den vollständigen Polymarket-Event-Link ein: ").strip()

    try:
        if "polymarket.com/event/" not in url:
            print("Ungültiges URL-Format")
            pause()
            return

        slug = url.split("/event/")[-1].split("?")[0].split("#")[0]
        print(f"Analysiere Slug: {slug}")

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
            print(f"Kein Markt mit Slug '{slug}' gefunden.")
            pause()
            return

        detailed_market = client.get_market(target_condition_id).get("market", {})
        simplified_markets = client.get_sampling_simplified_markets().get("data", [])
        simplified_data = next((m for m in simplified_markets if m["condition_id"] == target_condition_id), {})

        market_data = {
            "condition_id": target_condition_id,
            "slug": slug,
            "question": detailed_market.get("question", "N/A"),
            "category": detailed_market.get("category", "N/A"),
            "end_date": detailed_market.get("end_date_iso", "N/A")[:10],
            "yes_price": next((t["price"] for t in simplified_data.get("tokens", []) if t["outcome"] == "Yes"), "N/A"),
            "no_price": next((t["price"] for t in simplified_data.get("tokens", []) if t["outcome"] == "No"), "N/A"),
            "min_size": simplified_data.get("rewards", {}).get("min_size", "N/A"),
            "max_spread": simplified_data.get("rewards", {}).get("max_spread", "N/A"),
            "daily_reward": simplified_data.get("rewards", {}).get("rates", [{}])[0].get("rewards_daily_rate", "N/A"),
            "active": simplified_data.get("active", False),
            "closed": simplified_data.get("closed", False),
            "accepting_orders": simplified_data.get("accepting_orders", False)
        }

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

        print(f"\n Daten wurden erfolgreich in '{filename}' gespeichert.")
        print("Enthaltene Daten:")
        for key, value in market_data.items():
            print(f"{key:>15}: {value}")
    except Exception as e:
        print(f" Fehler: {str(e)}")
    pause()

def filter_for_info(client):
    """Filters information by condition_id."""
    clear_screen()
    display_header()
    condition_id = input("Bitte condition_id eingeben: ").strip()

    try:
        print(client.get_market(condition_id))
    except Exception as e:
        print(f" Fehler: {str(e)}")
    pause()

def fetch_all_market_data(client):
    """Fetches data for all markets and saves to CSV."""
    clear_screen()
    display_header()
    try:
        response = client.get_sampling_markets()
        markets = response.get("data", []) if isinstance(response, dict) else response

        if not markets:
            print("Keine Marktdaten von der API erhalten.")
            pause()
            return

        filename = "all_market_data.csv"
        with open(filename, "w", newline="", encoding="utf-8") as csvfile:
            csvwriter = csv.writer(csvfile)
            csvwriter.writerow(["Event", "Market End", "CONDITION_ID", "Token_ID", "Outcome", "Price"])
            for market in markets:
                event = market.get("market_slug", "N/A")
                market_end = market.get("end_date_iso", "N/A")
                condition_id = market.get("condition_id", "N/A")
                tokens = market.get("tokens", [])
                for token in tokens:
                    token_id = token.get("token_id", "N/A")
                    outcome = token.get("outcome", "N/A")
                    price = token.get("price", "N/A")
                    csvwriter.writerow([event, market_end, condition_id, token_id, outcome, price])
        print(f"Alle Marktdaten wurden erfolgreich in '{filename}' gespeichert.")
    except Exception as e:
        print(f"Fehler beim Abrufen der Marktdaten: {str(e)}")
    pause()

def main():
    """Main function to run the PolyBot CLI."""
    try:
        load_dotenv()
        required_vars = [
            "POLYMARKET_HOST",
            "POLYMARKET_KEY",
            "POLYMARKET_API_KEY",
            "POLYMARKET_API_SECRET",
            "POLYMARKET_API_PASSPHRASE"
        ]
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        if missing_vars:
            raise ValueError(f"Fehlende Umgebungsvariablen: {', '.join(missing_vars)}")

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

        while True:
            clear_screen()
            display_header()
            print("Optionen:")
            print("1. Märkte abrufen (Filter: Enddatum / Stichwort)")
            print("2. Info via Polymarket-Link abrufen")
            print("3. Filtern via condition_id")
            print("4. API-Endpunkte (Rohdaten)")
            print("5. Alle Marktdaten abrufen")
            print("6. Orderbook analysieren")
            print("7. Beenden")
            choice = input("Option wählen: ").strip()

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
                retrieve_orderbook(client)
            elif choice == '7':
                print("Programm wird beendet...")
                sys.exit(0)
            else:
                print("Ungültige Option. Bitte erneut versuchen.")
                pause()
    except ValueError as ve:
        print(f"Konfigurationsfehler: {str(ve)}")
    except Exception as e:
        print(f"Ein kritischer Fehler ist aufgetreten: {str(e)}")
    pause()

if __name__ == "__main__":
    main()