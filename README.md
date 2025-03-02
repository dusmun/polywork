# PolyBot CLI

PolyBot CLI is a command-line interface tool designed to interact with the Polymarket platform via a CLOB client. It provides a suite of features that allow you to retrieve market data, analyze order books, and place various types of orders quickly and efficiently. With built-in scheduling and CSV-based batch execution, PolyBot is optimized for speed and adaptability, helping you gain a competitive edge in fast-paced markets.

---

## Table of Contents

- [Features](#features)
- [Requirements](#requirements)
- [Installation & Setup](#installation--setup)
- [Usage](#usage)
  - [Main Menu](#main-menu)
  - [Retrieve Info](#retrieve-info)
  - [Place Orders](#place-orders)
  - [CSV Orders & Scheduling](#csv-orders--scheduling)
  - [Cancel All Orders](#cancel-all-orders)
- [CSV Order Format Reference](#csv-order-format-reference)
- [Customization](#customization)
- [Troubleshooting](#troubleshooting)
- [License](#license)

---

## Features

- **Market Data Retrieval and Analysis**
  - Retrieve and filter market data based on end dates or keywords.
  - Analyze market details by fetching data from Polymarket links.
  - Visualize the order book (bids/asks) with detailed depth analysis and liquidity overview.

- **Order Placement**
  - **FOK (Fill-Or-Kill) Orders:** Create market orders that execute immediately for a specified USD amount.
  - **GTC (Good-Til-Cancelled) Orders:** Place limit orders by specifying a price and the number of tokens.
  - **GTD (Good-Til-Date) Orders:** Place limit orders with an expiration time.
  - **FOK_MAX Orders:** A special market order that sweeps through any ask orders below a specified maximum price until your USD budget is met.

- **CSV-Based Order Execution**
  - **Run CSV Orders (Immediate Execution):** Execute orders stored in a CSV file instantly for ultra-fast processing.
  - **Scheduled Orders:** Schedule orders for future execution; these are stored in a CSV file and run at the designated time.

- **Order Management**
  - **Cancel All Outstanding Orders:** Quickly cancel all open orders to mitigate risk or react to sudden market changes.

---

## Requirements

- **Python 3.x**
- **Python Packages:**
  - py_clob_client (for interacting with the Polymarket API)
  - python-dotenv (for loading environment variables)
  - colorama (for colored terminal output)
- **Environment Variables:**
  - POLYMARKET_HOST
  - POLYMARKET_KEY
  - POLYMARKET_API_KEY
  - POLYMARKET_API_SECRET
  - POLYMARKET_API_PASSPHRASE
  - POLYMARKET_PROXY_ADDRESS

---

## Installation & Setup

1. **Clone the Repository:**
   \`\`\`bash
   git clone https://github.com/yourusername/polybot-cli.git
   cd polybot-cli
   \`\`\`

2. **Install Dependencies:**
   \`\`\`bash
   pip install -r requirements.txt
   \`\`\`

3. **Configure Environment Variables:**
   Create a \`.env\` file in the project root and add your Polymarket API credentials:
   \`\`\`env
   POLYMARKET_HOST=your_host_url
   POLYMARKET_KEY=your_key
   POLYMARKET_API_KEY=your_api_key
   POLYMARKET_API_SECRET=your_api_secret
   POLYMARKET_API_PASSPHRASE=your_api_passphrase
   POLYMARKET_PROXY_ADDRESS=your_proxy_address
   \`\`\`

---

## Usage

### Main Menu

When you run the script, the main menu displays the following options:

- **Run CSV Orders (Immediate Execution):** Execute orders from a CSV file instantly for ultra-fast order placement.
- **Retrieve Info:** Access market information, including order book visualizations and detailed market analysis.
- **Place Orders:** Place various types of orders (FOK, GTC, GTD, FOK_MAX) and manage scheduled orders.
- **Exit:** Exit the program.

### Retrieve Info

- Filter markets by end date or keyword.
- Retrieve detailed info from a Polymarket event link.
- Filter market information by condition ID.
- Display raw API outputs.
- Download all market data as a CSV.
- Visualize the current order book along with liquidity analysis.

### Place Orders

- **Create Buy Order:** Place a new order by selecting from FOK, GTC, or GTD order types.
- **Buy Under Maximum Price Order:** Sweep the order book to fill any ask orders below a specified maximum price.
- **Schedule Order:** Schedule an order for future execution; the order is stored in a CSV file.
- **Execute Scheduled Orders:** Execute scheduled orders from the CSV file at their designated time.
- **Run CSV Orders (Immediate Execution):** Execute orders stored in a dedicated CSV file immediately.
- **Cancel All Outstanding Orders:** Quickly cancel all active orders if needed.

---

## CSV Orders & Scheduling

### Immediate CSV Orders

- The file \`orders_to_run.csv\` is used for immediate order execution.
- The bot processes each order in the file instantly.

### Scheduled Orders

- Orders scheduled for future execution are saved in \`scheduled_tasks.csv\`.
- The system will automatically execute them at the scheduled time.

### Cancel All Orders

This feature quickly cancels all your open orders to help you react in volatile market conditions or correct any errors.

---

## CSV Order Format Reference

Example CSV file (\`example_orders.csv\`):
\`\`\`csv
token_id,order_type,amount,price,size,expire_seconds
TOKEN123,FOK,50,,,
TOKEN456,GTC,,0.15,10,
TOKEN789,GTD,,0.12,5,300
TOKENABC,FOK_MAX,100,0.13,,
\`\`\`

### Order Type Breakdown

- **FOK Order:**
  - \`token_id\`: Unique asset identifier.
  - \`order_type\`: \`FOK\`
  - \`amount\`: USD amount to spend.

- **GTC Order:**
  - \`token_id\`: Unique asset identifier.
  - \`order_type\`: \`GTC\`
  - \`price\`: Desired price per token.
  - \`size\`: Number of tokens.

- **GTD Order:**
  - \`token_id\`: Unique asset identifier.
  - \`order_type\`: \`GTD\`
  - \`price\`: Desired price per token.
  - \`size\`: Number of tokens.
  - \`expire_seconds\`: Order expiration time (in seconds).

- **FOK_MAX Order:**
  - \`token_id\`: Unique asset identifier.
  - \`order_type\`: \`FOK_MAX\`
  - \`amount\`: USD budget to spend.
  - \`price\`: Maximum acceptable price per token.

---

## Customization

- Add new order types or adjust existing ones.
- Integrate dynamic order adjustments based on market conditions.
- Expand market data retrieval capabilities.
- Customize order execution logic to fit specific trading strategies.

---

## Troubleshooting

- Ensure your \`.env\` file is correctly set up with all required variables.
- Verify API credentials and network access.
- Confirm correct CSV file formatting and location.

---

## License

This project is licensed. Contact for details.