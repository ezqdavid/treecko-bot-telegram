# Treecko Finance Bot 🌿

A personal finance Telegram bot that processes MercadoPago transaction receipts, stores them in SQLite, and syncs to Google Sheets for reporting.

## Features

- 📄 **PDF Processing**: Parse MercadoPago transaction receipts
- 💾 **SQLite Storage**: Store all transactions in a local database
- 📊 **Google Sheets Sync**: Automatically add transactions to a Google Sheet for reporting
- 🤖 **Telegram Interface**: Easy-to-use bot commands

## Setup

### Prerequisites

- Python 3.10+
- A Telegram Bot Token (from [@BotFather](https://t.me/BotFather))
- (Optional) Google Cloud Service Account for Sheets integration

### Installation

1. Clone the repository:
```bash
git clone https://github.com/ezqdavid/treecko-bot-telegram.git
cd treecko-bot-telegram
```

2. Create a virtual environment and install dependencies:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. Copy the environment file and configure:
```bash
cp .env.example .env
```

4. Edit `.env` with your credentials:
```env
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
GOOGLE_CREDENTIALS_PATH=credentials.json
GOOGLE_SHEET_ID=your_google_sheet_id_here
DATABASE_PATH=transactions.db
```

### Google Sheets Setup (Optional)

1. Create a project in [Google Cloud Console](https://console.cloud.google.com/)
2. Enable the Google Sheets API and Google Drive API
3. Create a Service Account and download the credentials JSON file
4. Save the credentials file as `credentials.json` in the project root
5. Create a Google Sheet and share it with the service account email
6. Copy the Sheet ID from the URL and add it to your `.env`

## Usage

### Running the Bot

```bash
# Using pip
python -m treecko_bot.main

# Or after installing the package
pip install -e .
treecko-bot
```

### Bot Commands

- `/start` - Welcome message and bot overview
- `/help` - Get help with using the bot
- `/status` - Check the configuration status

### Processing Transactions

1. Download your MercadoPago transaction receipt as PDF
2. Send the PDF to the bot in Telegram
3. The bot will:
   - Extract transaction details (date, amount, description, etc.)
   - Store in SQLite database
   - Add to Google Sheets (if configured)
   - Reply with a summary

## Project Structure

```
treecko-bot-telegram/
├── src/
│   └── treecko_bot/
│       ├── __init__.py
│       ├── bot.py          # Telegram bot handlers
│       ├── config.py       # Configuration management
│       ├── database.py     # SQLite database operations
│       ├── main.py         # Entry point
│       ├── pdf_parser.py   # MercadoPago PDF parser
│       └── sheets.py       # Google Sheets integration
├── .env.example
├── pyproject.toml
├── README.md
└── requirements.txt
```

## Database Schema

The SQLite database stores transactions with the following fields:

| Field | Type | Description |
|-------|------|-------------|
| id | Integer | Primary key |
| transaction_id | String | MercadoPago transaction ID |
| date | DateTime | Transaction date |
| description | String | Transaction description |
| amount | Float | Transaction amount |
| transaction_type | String | "income" or "expense" |
| category | String | Transaction category |
| merchant | String | Merchant name |
| raw_text | String | Raw PDF text |
| created_at | DateTime | Record creation time |

## License

MIT License