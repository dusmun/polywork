#!/usr/bin/env python3
import os
import csv
import sys
import time
from datetime import datetime
from dotenv import load_dotenv
from py_clob_client.client import ClobClient
from py_clob_client.clob_types import ApiCreds, OrderArgs, MarketOrderArgs, OrderType
from py_clob_client.constants import AMOY
from py_clob_client.order_builder.constants import BUY
from colorama import init, Fore, Style

init(autoreset=True)

CSV_FILENAME = "scheduled_tasks.csv"

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
    print(Fore.CYAN + header)

def pause():
    """Pauses the execution until the user presses Enter."""
    input(Fore.YELLOW + "\nPress Enter to return to the main menu...")

def format_number(value: str) -> str:
    """Formats numeric strings with thousands separators."""
    try:
        num = float(value)
        return f"{num:,.2f}"
    except ValueError:
        return value

def display_orderbook_table(orders: list, order_type: str) -> None:
    """Displays bids/asks in a formatted table."""
    print(Fore.MAGENTA + f"\n{' ' * 16}{order_type.upper()} ORDERS")
    print(Fore.MAGENTA + f"{'Price':<12} | {'Size':<14} | {'Liquidity':<14}")
    print(Fore.MAGENTA + "-" * 45)
    for order in orders[:10]:  # Show top 10 orders
        price = format_number(order.price)
        size = format_number(order.size)
        liquidity = float(order.price) * float(order.size)
        print(Fore.MAGENTA + f"{price:<12} | {size:<14} | {format_number(str(liquidity)):<14}")

def retrieve_orderbook(client):
    """Displays detailed orderbook analysis with market depth visualization."""
    clear_screen()
    display_header()
    try:
        token_id = input(Fore.YELLOW + "Enter token ID: ").strip()
        orderbook = client.get_order_book(token_id)
        # Metadata Section
        print(Fore.GREEN + f"\n{' MARKET ANALYSIS ':=^50}")
        print(Fore.GREEN + f"Asset ID: {orderbook.asset_id}")
        print(Fore.GREEN + f"Timestamp: {datetime.fromtimestamp(int(orderbook.timestamp) / 1000):%Y-%m-%d %H:%M:%S}")
        print(Fore.GREEN + f"Market Hash: {orderbook.hash[:12]}...{orderbook.hash[-12:]}\n")
        # Process orders
        sorted_bids = sorted(orderbook.bids, key=lambda x: float(x.price), reverse=True)
        sorted_asks = sorted(orderbook.asks, key=lambda x: float(x.price))
        # Best Prices Section
        best_bid = float(sorted_bids[0].price) if sorted_bids else 0
        best_ask = float(sorted_asks[0].price) if sorted_asks else 0
        spread = best_ask - best_bid if best_bid and best_ask else 0
        print(Fore.BLUE + f"{' Best Bid ':-^23} | {' Best Ask ':-^23} | {' Spread ':-^15}")
        print(Fore.BLUE + f"{best_bid:^20.4f} | {best_ask:^20.4f} | {spread:^13.4f}")
        # Orderbook Visualization
        display_orderbook_table(sorted_bids, "Bid")
        display_orderbook_table(sorted_asks, "Ask")
        # Liquidity Analysis
        total_bid_liquidity = sum(float(b.price) * float(b.size) for b in sorted_bids)
        total_ask_liquidity = sum(float(a.price) * float(a.size) for a in sorted_asks)
        print(Fore.GREEN + f"\n{' LIQUIDITY ':=^50}")
        print(Fore.GREEN + f"Total Bid Liquidity: {format_number(str(total_bid_liquidity))} ETH")
        print(Fore.GREEN + f"Total Ask Liquidity: {format_number(str(total_ask_liquidity))} ETH")
    except Exception as e:
        print(Fore.RED + f"\nError: {str(e)}")
    pause()

def display_api_calls(client):
    """Calls various API methods and prints their raw outputs."""
    clear_screen()
    display_header()
    print(Fore.GREEN + "Calling API endpoints and displaying raw outputs...\n")
    try:
        print(Fore.CYAN + "\nclient.get_sampling_markets():")
        print(client.get_sampling_markets())
    except Exception as e:
        print(Fore.RED + f"Error calling API: {str(e)}")
    pause()

def filter_markets(client):
    """Filters markets by end date or keyword."""
    clear_screen()
    display_header()
    print(Fore.GREEN + "Filter Criteria:")
    print(Fore.GREEN + "1. End Date")
    print(Fore.GREEN + "2. Keyword")
    option = input(Fore.YELLOW + "Select an option (1 or 2): ").strip()
    try:
        sampling_response = client.get_sampling_markets()
        markets = sampling_response.get("data", []) if isinstance(sampling_response, dict) else sampling_response
    except Exception as e:
        print(Fore.RED + f"Error retrieving markets: {str(e)}")
        pause()
        return
    if option == "1":
        date_filter = input(Fore.YELLOW + "Enter end date (YYYY-MM-DD): ").strip()
        date_filter = datetime.strptime(date_filter, "%Y-%m-%d").date()
        filtered = []
        for m in markets:
            date = m.get("end_date_iso")
            if date:
                date = datetime.strptime(date[:10], "%Y-%m-%d").date()
                if date_filter >= date >= datetime.now().date():
                    print(Fore.CYAN + f"Event: {m.get('market_slug', 'N/A')} | End Date: {date}")
                    filtered.append(m)
        if not filtered:
            print(Fore.RED + "No markets found with that end date.")
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
                print(Fore.GREEN + f"CSV file '{filename}' created successfully.")
            except Exception as e:
                print(Fore.RED + f"Error writing CSV file: {str(e)}")
    elif option == "2":
        keyword = input(Fore.YELLOW + "Keyword (Filter): ").strip().lower()
        filtered = [m for m in markets if keyword in m.get("market_slug", "").lower()]
        if not filtered:
            print(Fore.RED + "No markets found with that keyword.")
        else:
            for m in filtered:
                market_slug = m.get("market_slug", "N/A")
                condition_id = m.get("condition_id", "N/A")
                print(Fore.CYAN + f"Event: {market_slug} | condition_id: {condition_id}")
    else:
        print(Fore.RED + "Invalid selection.")
    pause()

def fetch_info_from_url(client):
    """Extracts market data from a Polymarket event link."""
    clear_screen()
    display_header()
    print(Fore.GREEN + "--- Polymarket Link Analysis ---")
    url = input(Fore.YELLOW + "Enter the full Polymarket event link: ").strip()
    try:
        if "polymarket.com/event/" not in url:
            print(Fore.RED + "Invalid URL format")
            pause()
            return
        slug = url.split("/event/")[-1].split("?")[0].split("#")[0]
        print(Fore.CYAN + f"Analyzing slug: {slug}")
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
            print(Fore.RED + f"No market found with slug '{slug}'.")
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
        print(Fore.GREEN + f"\nData saved successfully to '{filename}'.")
        print(Fore.CYAN + "Data included:")
        for key, value in market_data.items():
            print(Fore.CYAN + f"{key:>15}: {value}")
    except Exception as e:
        print(Fore.RED + f"Error: {str(e)}")
    pause()

def filter_for_info(client):
    """Filters information by condition_id."""
    clear_screen()
    display_header()
    condition_id = input(Fore.YELLOW + "Enter condition_id: ").strip()
    try:
        print(client.get_market(condition_id))
    except Exception as e:
        print(Fore.RED + f"Error: {str(e)}")
    pause()

def fetch_all_market_data(client):
    """Fetches data for all markets and saves it to CSV."""
    clear_screen()
    display_header()
    try:
        response = client.get_sampling_markets()
        markets = response.get("data", []) if isinstance(response, dict) else response
        if not markets:
            print(Fore.RED + "No market data received from API.")
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
        print(Fore.GREEN + f"All market data successfully saved to '{filename}'.")
    except Exception as e:
        print(Fore.RED + f"Error retrieving market data: {str(e)}")
    pause()

def create_buy_order(client):
    """Handles creation of buy orders with FOK, GTC, and GTD options."""
    clear_screen()
    display_header()
    print(Fore.GREEN + "--- Create Buy Order ---\n")
    print(Fore.GREEN + "Select order type:")
    print(Fore.GREEN + "1. FOK (Market Order)")
    print(Fore.GREEN + "2. GTC (Limit Order)")
    print(Fore.GREEN + "3. GTD (Limit Order with Expiration)")
    print(Fore.GREEN + "4. Back to Menu")
    order_type_choice = input(Fore.YELLOW + "Choose an option: ").strip()
    if order_type_choice == '4':
        return
    try:
        token_id = input(Fore.YELLOW + "\nEnter Token ID: ").strip()
        if order_type_choice == '1':
            amount = float(input(Fore.YELLOW + "Enter amount in USD: "))
            order_args = MarketOrderArgs(
                token_id=token_id,
                amount=amount,
                side=BUY,
            )
            signed_order = client.create_market_order(order_args)
            resp = client.post_order(signed_order, OrderType.FOK)
        elif order_type_choice == '2':
            price = float(input(Fore.YELLOW + "Enter price per token: "))
            size = float(input(Fore.YELLOW + "Enter number of tokens: "))
            order_args = OrderArgs(
                price=price,
                size=size,
                side=BUY,
                token_id=token_id,
            )
            signed_order = client.create_order(order_args)
            resp = client.post_order(signed_order, OrderType.GTC)
        elif order_type_choice == '3':
            price = float(input(Fore.YELLOW + "Enter price per token: "))
            size = float(input(Fore.YELLOW + "Enter number of tokens: "))
            expire_seconds = int(input(Fore.YELLOW + "Enter valid duration in seconds: "))
            expiration = int(datetime.now().timestamp()) + expire_seconds + 60
            order_args = OrderArgs(
                price=price,
                size=size,
                side=BUY,
                token_id=token_id,
                expiration=str(expiration),
            )
            signed_order = client.create_order(order_args)
            resp = client.post_order(signed_order, OrderType.GTD)
        else:
            print(Fore.RED + "Invalid selection.")
            pause()
            return
        print(Fore.GREEN + "\nResponse from server:")
        print(Fore.CYAN + f"Success: {resp.get('success', 'N/A')}")
        print(Fore.CYAN + f"Error message: {resp.get('errorMsg', 'None')}")
        print(Fore.CYAN + f"Order ID: {resp.get('orderID', 'N/A')}")
        print(Fore.CYAN + f"Transaction hashes: {', '.join(resp.get('transactionsHashes', []))}")
        print(Fore.CYAN + f"Status: {resp.get('status', 'N/A')}")
    except Exception as e:
        print(Fore.RED + f"\nError creating order: {str(e)}")
    pause()

def schedule_task(client):
    """Interactively schedule an order and save it to a CSV file."""
    clear_screen()
    display_header()
    print(Fore.GREEN + "--- Schedule Order ---\n")
    scheduled_str = input(Fore.YELLOW + "Enter planned date and time (YYYY-MM-DD HH:MM): ").strip()
    try:
        scheduled_datetime = datetime.strptime(scheduled_str, "%Y-%m-%d %H:%M")
    except ValueError:
        print(Fore.RED + "Invalid date/time format.")
        pause()
        return
    token_id = input(Fore.YELLOW + "Enter Token ID: ").strip()
    print(Fore.GREEN + "Select order type:")
    print(Fore.GREEN + "1. FOK (Market Order)")
    print(Fore.GREEN + "2. GTC (Limit Order)")
    print(Fore.GREEN + "3. GTD (Limit Order with Expiration)")
    order_type_choice = input(Fore.YELLOW + "Option: ").strip()
    if order_type_choice == '1':
        order_type = "FOK"
        amount = input(Fore.YELLOW + "Enter amount in USD: ").strip()
        task = {
            "scheduled_datetime": scheduled_datetime.strftime("%Y-%m-%d %H:%M"),
            "token_id": token_id,
            "order_type": order_type,
            "amount": amount,
            "price": "",
            "size": "",
            "expire_seconds": ""
        }
    elif order_type_choice == '2':
        order_type = "GTC"
        price = input(Fore.YELLOW + "Enter price per token: ").strip()
        size = input(Fore.YELLOW + "Enter number of tokens: ").strip()
        task = {
            "scheduled_datetime": scheduled_datetime.strftime("%Y-%m-%d %H:%M"),
            "token_id": token_id,
            "order_type": order_type,
            "amount": "",
            "price": price,
            "size": size,
            "expire_seconds": ""
        }
    elif order_type_choice == '3':
        order_type = "GTD"
        price = input(Fore.YELLOW + "Enter price per token: ").strip()
        size = input(Fore.YELLOW + "Enter number of tokens: ").strip()
        expire_seconds = input(Fore.YELLOW + "Enter valid duration in seconds: ").strip()
        task = {
            "scheduled_datetime": scheduled_datetime.strftime("%Y-%m-%d %H:%M"),
            "token_id": token_id,
            "order_type": order_type,
            "amount": "",
            "price": price,
            "size": size,
            "expire_seconds": expire_seconds
        }
    else:
        print(Fore.RED + "Invalid selection.")
        pause()
        return
    csv_filename = CSV_FILENAME
    file_exists = os.path.isfile(csv_filename)
    try:
        with open(csv_filename, "a", newline="", encoding="utf-8") as csvfile:
            fieldnames = ["scheduled_datetime", "token_id", "order_type", "amount", "price", "size", "expire_seconds"]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            if not file_exists:
                writer.writeheader()
            writer.writerow(task)
        print(Fore.GREEN + "Order successfully scheduled and saved to CSV.")
    except Exception as e:
        print(Fore.RED + f"Error writing to CSV file: {str(e)}")
    pause()

def execute_scheduled_order(client, task):
    """Executes a scheduled order based on CSV data."""
    print(Fore.CYAN + f"Executing scheduled order: Token ID: {task['token_id']}, Order Type: {task['order_type']}")
    try:
        if task["order_type"].upper() == "FOK":
            amount = float(task["amount"])
            order_args = MarketOrderArgs(
                token_id=task["token_id"],
                amount=amount,
                side=BUY,
            )
            signed_order = client.create_market_order(order_args)
            resp = client.post_order(signed_order, OrderType.FOK)
        elif task["order_type"].upper() == "GTC":
            price = float(task["price"])
            size = float(task["size"])
            order_args = OrderArgs(
                price=price,
                size=size,
                side=BUY,
                token_id=task["token_id"],
            )
            signed_order = client.create_order(order_args)
            resp = client.post_order(signed_order, OrderType.GTC)
        elif task["order_type"].upper() == "GTD":
            price = float(task["price"])
            size = float(task["size"])
            expire_seconds = int(task["expire_seconds"])
            expiration = int(datetime.now().timestamp()) + expire_seconds + 60
            order_args = OrderArgs(
                price=price,
                size=size,
                side=BUY,
                token_id=task["token_id"],
                expiration=str(expiration),
            )
            signed_order = client.create_order(order_args)
            resp = client.post_order(signed_order, OrderType.GTD)
        else:
            print(Fore.RED + "Unknown order type.")
            return
        print(Fore.GREEN + "Order successfully executed!")
        print(Fore.CYAN + f"Response from server: {resp}")
    except Exception as e:
        print(Fore.RED + f"Error executing order: {str(e)}")

def print_scheduled_tasks_overview(tasks):
    """Prints a structured overview of scheduled tasks."""
    print(Fore.BLUE + "\nScheduled Tasks Overview:")
    print(Fore.BLUE + f"{'Execution Time':<20} | {'Token ID':<10} | {'Order Type':<8} | Details")
    print(Fore.BLUE + "-" * 60)
    for task in sorted(tasks, key=lambda x: datetime.strptime(x["scheduled_datetime"], "%Y-%m-%d %H:%M")):
        exec_time = task["scheduled_datetime"]
        token = task["token_id"]
        order_type = task["order_type"]
        if order_type.upper() == "FOK":
            details = f"Amount: {task['amount']} USD"
        else:
            details = f"Price: {task['price']} | Size: {task['size']}"
        print(Fore.BLUE + f"{exec_time:<20} | {token:<10} | {order_type:<8} | {details}")
    print()

def run_csv_tasks(client):
    """Reads tasks from CSV and executes them at the scheduled time."""
    clear_screen()
    display_header()
    csv_filename = CSV_FILENAME
    if not os.path.isfile(csv_filename):
        print(Fore.RED + "No CSV tasks found.")
        pause()
        return
    # Load tasks
    tasks = []
    try:
        with open(csv_filename, "r", newline="", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                tasks.append(row)
    except Exception as e:
        print(Fore.RED + f"Error reading CSV file: {str(e)}")
        pause()
        return
    if not tasks:
        print(Fore.RED + "No scheduled tasks found.")
        pause()
        return
    # Print scheduled tasks overview
    print_scheduled_tasks_overview(tasks)
    print(Fore.GREEN + "Starting task runner. Press Ctrl+C to abort.\n")
    try:
        while tasks:
            now = datetime.now()
            remaining_tasks = []
            for task in tasks:
                scheduled_time = datetime.strptime(task["scheduled_datetime"], "%Y-%m-%d %H:%M")
                if now >= scheduled_time:
                    print(Fore.CYAN + f"\n[{now.strftime('%Y-%m-%d %H:%M:%S')}] Executing task scheduled for {task['scheduled_datetime']}")
                    execute_scheduled_order(client, task)
                else:
                    remaining_tasks.append(task)
            tasks = remaining_tasks
            # Update CSV with remaining tasks
            with open(csv_filename, "w", newline="", encoding="utf-8") as csvfile:
                fieldnames = ["scheduled_datetime", "token_id", "order_type", "amount", "price", "size", "expire_seconds"]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                for task in tasks:
                    writer.writerow(task)
            if tasks:
                time.sleep(60)
            else:
                print(Fore.GREEN + "All tasks have been executed.")
    except KeyboardInterrupt:
        print(Fore.RED + "\nTask runner aborted.")
    pause()

def create_buy_under_max_price(client):
    """Buy tokens by filling every ask underneath a maximum price."""
    clear_screen()
    display_header()
    print(Fore.GREEN + "--- Buy Under Maximum Price Order ---\n")
    token_id = input(Fore.YELLOW + "Enter Token ID: ").strip()
    try:
        max_price = float(input(Fore.YELLOW + "Enter maximum acceptable price per token: "))
    except ValueError:
        print(Fore.RED + "Invalid maximum price.")
        pause()
        return
    try:
        total_amount = float(input(Fore.YELLOW + "Enter total token amount to buy: "))
    except ValueError:
        print(Fore.RED + "Invalid token amount.")
        pause()
        return
    try:
        # Retrieve the order book for the given token
        orderbook = client.get_order_book(token_id)
    except Exception as e:
        print(Fore.RED + f"Error retrieving order book: {str(e)}")
        pause()
        return
    if not orderbook.asks:
        print(Fore.RED + "No ask orders available.")
        pause()
        return
    # Sort asks in ascending order (lowest price first)
    sorted_asks = sorted(orderbook.asks, key=lambda x: float(x.price))
    remaining = total_amount
    print(Fore.CYAN + f"\nAttempting to fill {total_amount} tokens with asks <= {max_price}...\n")
    # Iterate over asks until we either run out or the ask price exceeds max_price.
    for ask in sorted_asks:
        ask_price = float(ask.price)
        if ask_price > max_price:
            break  # All subsequent asks are above the max price
        available_size = float(ask.size)
        if available_size <= 0:
            continue
        size_to_buy = min(remaining, available_size)
        # Create a limit order at the ask price for the determined size
        order_args = OrderArgs(
            price=ask_price,
            size=size_to_buy,
            side=BUY,
            token_id=token_id
        )
        try:
            signed_order = client.create_order(order_args)
            resp = client.post_order(signed_order, OrderType.GTC)
            print(Fore.GREEN + f"Order placed at {ask_price:.4f} for {size_to_buy} tokens.")
        except Exception as e:
            print(Fore.RED + f"Error placing order at price {ask_price:.4f}: {str(e)}")
        remaining -= size_to_buy
        if remaining <= 0:
            break
    if remaining > 0:
        print(Fore.YELLOW + f"\nUnfilled amount: {remaining} tokens (insufficient asks under {max_price}).")
    else:
        print(Fore.GREEN + "\nOrder successfully filled for the specified amount.")
    pause()

def run_csv_orders(client):
    """Executes orders specified in a CSV file immediately for high-speed order execution."""
    clear_screen()
    display_header()
    csv_filename = "orders_to_run.csv"  # Use a dedicated CSV for this purpose
    if not os.path.isfile(csv_filename):
        print(Fore.RED + f"No CSV orders found in '{csv_filename}'.")
        pause()
        return

    orders = []
    try:
        with open(csv_filename, "r", newline="", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                orders.append(row)
    except Exception as e:
        print(Fore.RED + f"Error reading CSV file: {str(e)}")
        pause()
        return

    if not orders:
        print(Fore.RED + "No orders found in CSV.")
        pause()
        return

    print(Fore.BLUE + f"Executing {len(orders)} order(s) from CSV...\n")
    for order in orders:
        token_id = order.get("token_id")
        order_type = order.get("order_type", "").upper()
        try:
            if order_type == "FOK":
                # Standard market order without price filtering.
                amount = float(order.get("amount", 0))
                order_args = MarketOrderArgs(
                    token_id=token_id,
                    amount=amount,
                    side=BUY,
                )
                signed_order = client.create_market_order(order_args)
                resp = client.post_order(signed_order, OrderType.FOK)
            elif order_type == "GTC":
                price = float(order.get("price", 0))
                size = float(order.get("size", 0))
                order_args = OrderArgs(
                    price=price,
                    size=size,
                    side=BUY,
                    token_id=token_id,
                )
                signed_order = client.create_order(order_args)
                resp = client.post_order(signed_order, OrderType.GTC)
            elif order_type == "GTD":
                price = float(order.get("price", 0))
                size = float(order.get("size", 0))
                expire_seconds = int(order.get("expire_seconds", 0))
                expiration = int(datetime.now().timestamp()) + expire_seconds + 60
                order_args = OrderArgs(
                    price=price,
                    size=size,
                    side=BUY,
                    token_id=token_id,
                    expiration=str(expiration),
                )
                signed_order = client.create_order(order_args)
                resp = client.post_order(signed_order, OrderType.GTD)
            elif order_type == "FOK_MAX":
                # New option: Market order that fills any ask under a max acceptable price
                # "amount" is the USD budget and "price" is the maximum acceptable price per token.
                max_price = float(order.get("price", 0))
                usd_budget = float(order.get("amount", 0))
                # Retrieve the order book for the token.
                orderbook = client.get_order_book(token_id)
                if not orderbook.asks:
                    print(Fore.RED + f"No ask orders available for token {token_id}.")
                    continue
                # Sort asks in ascending order.
                sorted_asks = sorted(orderbook.asks, key=lambda x: float(x.price))
                remaining_usd = usd_budget
                print(Fore.CYAN + f"\nAttempting to spend ${usd_budget:.2f} on token {token_id} with max price ${max_price:.4f}...")
                for ask in sorted_asks:
                    ask_price = float(ask.price)
                    if ask_price > max_price:
                        break  # Subsequent asks exceed max price.
                    available_size = float(ask.size)
                    if available_size <= 0:
                        continue
                    # Determine maximum tokens that can be purchased at this ask with remaining USD.
                    max_tokens = remaining_usd / ask_price
                    # Buy no more than available tokens.
                    tokens_to_buy = min(max_tokens, available_size)
                    if tokens_to_buy <= 0:
                        continue
                    # Create a limit order at the ask price for tokens_to_buy.
                    order_args = OrderArgs(
                        price=ask_price,
                        size=tokens_to_buy,
                        side=BUY,
                        token_id=token_id
                    )
                    try:
                        signed_order = client.create_order(order_args)
                        resp = client.post_order(signed_order, OrderType.GTC)
                        print(Fore.GREEN + f"Order placed at {ask_price:.4f} for {tokens_to_buy:.4f} tokens.")
                    except Exception as e:
                        print(Fore.RED + f"Error placing order at price {ask_price:.4f}: {str(e)}")
                    # Deduct the spent USD amount.
                    remaining_usd -= tokens_to_buy * ask_price
                    if remaining_usd <= 0:
                        break
                if remaining_usd > 0:
                    print(Fore.YELLOW + f"\nUnspent USD: ${remaining_usd:.2f} (Not enough asks under ${max_price:.4f}).")
                else:
                    print(Fore.GREEN + "\nMarket order under maximum price successfully filled for the specified amount.")
            else:
                print(Fore.RED + f"Unknown order type '{order_type}' for token {token_id}. Skipping.")
                continue
            print(Fore.GREEN + f"Executed order for token {token_id} | Type: {order_type} | Response: {resp.get('status', 'N/A')}")
        except Exception as e:
            print(Fore.RED + f"Error executing order for token {token_id}: {str(e)}")
    pause()


def cancel_all_orders(client):
    """Cancels all outstanding orders quickly."""
    clear_screen()
    display_header()
    print(Fore.GREEN + "--- Cancel All Outstanding Orders ---\n")
    try:
        # Retrieve open orders. Adjust the API call if necessary.
        open_orders = client.get_open_orders()  # Hypothetical function; use your client's actual method.
        if not open_orders:
            print(Fore.YELLOW + "No outstanding orders found.")
        else:
            for order in open_orders:
                order_id = order.get("orderID") or order.get("order_id")
                if order_id:
                    try:
                        resp = client.cancel_order(order_id)
                        print(Fore.GREEN + f"Canceled order {order_id}: {resp.get('status', 'Unknown')}")
                    except Exception as e:
                        print(Fore.RED + f"Error canceling order {order_id}: {str(e)}")
            print(Fore.GREEN + "\nAll outstanding orders have been canceled.")
    except Exception as e:
        print(Fore.RED + f"Error retrieving open orders: {str(e)}")
    pause()

def info_menu(client):
    """Submenu for Retrieve Info functions."""
    while True:
        clear_screen()
        display_header()
        print(Fore.GREEN + "Retrieve Info Menu:")
        print(Fore.GREEN + "1. Retrieve Markets (Filter by end date / keyword)")
        print(Fore.GREEN + "2. Retrieve info from Polymarket Link")
        print(Fore.GREEN + "3. Filter info by condition_id")
        print(Fore.GREEN + "4. API Endpoints (Raw Data)")
        print(Fore.GREEN + "5. Fetch all market data")
        print(Fore.GREEN + "6. Analyze Orderbook")
        print(Fore.GREEN + "7. Back to Main Menu")
        choice = input(Fore.YELLOW + "Select option: ").strip()
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
            break
        else:
            print(Fore.RED + "Invalid option. Please try again.")
            pause()

def order_menu(client):
    """Submenu for Place Orders functions."""
    while True:
        clear_screen()
        display_header()
        print(Fore.GREEN + "Place Orders Menu:")
        print(Fore.GREEN + "1. Create Buy Order")
        print(Fore.GREEN + "2. Buy Under Maximum Price Order")
        print(Fore.GREEN + "3. Schedule Order")
        print(Fore.GREEN + "4. Execute Scheduled Orders")
        print(Fore.GREEN + "5. Run CSV Orders (Immediate Execution)")
        print(Fore.GREEN + "6. Cancel All Outstanding Orders")
        print(Fore.GREEN + "7. Back to Main Menu")
        choice = input(Fore.YELLOW + "Select option: ").strip()
        if choice == '1':
            create_buy_order(client)
        elif choice == '2':
            create_buy_under_max_price(client)
        elif choice == '3':
            schedule_task(client)
        elif choice == '4':
            run_csv_tasks(client)
        elif choice == '5':
            run_csv_orders(client)
        elif choice == '6':
            cancel_all_orders(client)
        elif choice == '7':
            break
        else:
            print(Fore.RED + "Invalid option. Please try again.")
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
            "POLYMARKET_API_PASSPHRASE",
            "POLYMARKET_PROXY_ADDRESS"
        ]
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        if missing_vars:
            raise ValueError(f"Missing environment variables: {', '.join(missing_vars)}")
        client = ClobClient(
            host=os.getenv("POLYMARKET_HOST"),
            key=os.getenv("POLYMARKET_KEY"),
            chain_id=137,
            creds=ApiCreds(
                api_key=os.getenv("POLYMARKET_API_KEY"),
                api_secret=os.getenv("POLYMARKET_API_SECRET"),
                api_passphrase=os.getenv("POLYMARKET_API_PASSPHRASE")
            ),
            signature_type=1,
            funder=os.getenv("POLYMARKET_PROXY_ADDRESS")
        )
        while True:
            clear_screen()
            display_header()
            print(Fore.GREEN + "Main Menu:")
            print(Fore.GREEN + "1. Run CSV Orders (Immediate Execution)")
            print(Fore.GREEN + "2. Retrieve Info")
            print(Fore.GREEN + "3. Place Orders")
            print(Fore.GREEN + "4. Exit")
            choice = input(Fore.YELLOW + "Select option: ").strip()
            if choice == '1':
                run_csv_orders(client)
            elif choice == '2':
                info_menu(client)
            elif choice == '3':
                order_menu(client)
            elif choice == '4':
                print(Fore.GREEN + "Exiting program...")
                sys.exit(0)
            else:
                print(Fore.RED + "Invalid option. Please try again.")
                pause()
    except ValueError as ve:
        print(Fore.RED + f"Configuration error: {str(ve)}")
    except Exception as e:
        print(Fore.RED + f"A critical error occurred: {str(e)}")
    pause()

if __name__ == "__main__":
    main()
