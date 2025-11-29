# Treecko Finance Bot 🌿

A personal finance Telegram bot that processes MercadoPago transaction receipts, stores them in SQLite, and syncs to Google Sheets for reporting.

## Features

- 📄 **PDF Processing**: Parse MercadoPago transaction receipts
- 💾 **SQLite Storage**: Store all transactions in a local database
- 📊 **Google Sheets Sync**: Automatically add transactions to a Google Sheet for reporting
- 🤖 **Telegram Interface**: Easy-to-use bot commands
- 🌐 **Webhook Support**: Ready for deployment on Google Cloud Run

## Prerequisites

- Python 3.10+
- Docker (for deployment)
- Google Cloud CLI (`gcloud`) for Cloud Run deployment
- A Telegram Bot Token (from [@BotFather](https://t.me/BotFather))
- (Optional) Google Cloud Service Account for Sheets integration
- (Optional) ngrok for local webhook testing

## Setup

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

4. Edit `.env` with your credentials (see Environment Variables section below).

### Google Sheets Setup (Optional)

1. Create a project in [Google Cloud Console](https://console.cloud.google.com/)
2. Enable the Google Sheets API and Google Drive API
3. Create a Service Account and download the credentials JSON file
4. Save the credentials file as `credentials.json` in the project root
5. Create a Google Sheet and share it with the service account email
6. Copy the Sheet ID from the URL and add it to your `.env`

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `TELEGRAM_BOT_TOKEN` | ✅ Yes | - | Your bot token from @BotFather |
| `WEBHOOK_BASE_URL` | No | - | Cloud Run URL (without path). If empty, bot uses polling mode |
| `PORT` | No | `8080` | HTTP server port (Cloud Run sets this automatically) |
| `GOOGLE_CREDENTIALS_PATH` | No | `credentials.json` | Path to Google service account JSON |
| `GOOGLE_SHEET_ID` | No | - | Google Sheet document ID |
| `DATABASE_PATH` | No | `transactions.db` | SQLite database file path |

## Running the Bot

### Option 1: Local Development (Polling Mode)

For simple local testing without setting up a webhook:

```bash
# Ensure .env has TELEGRAM_BOT_TOKEN set (and WEBHOOK_BASE_URL is empty)
python -m treecko_bot.main
```

### Option 2: Local Development with Webhook (using ngrok)

To test webhook functionality locally:

1. Install and start ngrok:
```bash
ngrok http 8080
```

2. Copy the HTTPS URL from ngrok (e.g., `https://abc123.ngrok.io`)

3. Update your `.env`:
```env
TELEGRAM_BOT_TOKEN=your_token
WEBHOOK_BASE_URL=https://abc123.ngrok.io
PORT=8080
```

4. Run the bot:
```bash
python -m treecko_bot.main
```

### Option 3: Using Docker locally

```bash
# Build the image
docker build -t treecko-bot .

# Run with polling mode (for testing)
docker run --env-file .env treecko-bot

# Or run with webhook mode (ngrok URL)
docker run -p 8080:8080 --env-file .env treecko-bot
```

## Deploy to Google Cloud Run

### Step 1: Authenticate with Google Cloud

```bash
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
```

### Step 2: Deploy to Cloud Run

Use source-based deployment (Cloud Run builds the container for you):

```bash
gcloud run deploy treecko-bot \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars TELEGRAM_BOT_TOKEN=YOUR_BOT_TOKEN
```

### Step 3: Set the Webhook URL

After deployment, Cloud Run provides a URL (e.g., `https://treecko-bot-abc123-uc.a.run.app`).

Update the service with the webhook URL:

```bash
gcloud run services update treecko-bot \
  --region us-central1 \
  --set-env-vars TELEGRAM_BOT_TOKEN=YOUR_BOT_TOKEN,WEBHOOK_BASE_URL=https://treecko-bot-abc123-uc.a.run.app
```

Alternatively, you can set both variables in a single deploy command if you know your Cloud Run URL beforehand.

### Step 4: Verify the Deployment

1. Check the Cloud Run logs:
```bash
gcloud run logs read --service treecko-bot --region us-central1
```

2. Send `/start` to your bot on Telegram - it should respond!

### Optional: Add Google Sheets Integration

If using Google Sheets, create a secret and mount it:

```bash
# Create a secret from your credentials file
gcloud secrets create google-credentials --data-file=credentials.json

# Grant Cloud Run access to the secret
gcloud secrets add-iam-policy-binding google-credentials \
  --member=serviceAccount:YOUR_PROJECT_NUMBER-compute@developer.gserviceaccount.com \
  --role=roles/secretmanager.secretAccessor

# Update the deployment
gcloud run services update treecko-bot \
  --region us-central1 \
  --set-secrets=/app/credentials.json=google-credentials:latest \
  --set-env-vars GOOGLE_CREDENTIALS_PATH=/app/credentials.json,GOOGLE_SHEET_ID=YOUR_SHEET_ID
```

## Bot Commands

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
├── tests/                  # Test files
├── .env.example
├── Dockerfile
├── pyproject.toml
├── README.md
└── requirements.txt
```

## Cost Notes

With webhook mode and low traffic:
- **Cloud Run**: Falls within the free tier (2 million requests/month, 360,000 GB-seconds of memory)
- **Container Registry/Artifact Registry**: Minimal storage costs
- The bot only runs when receiving messages (pay-per-use model)

For personal use with minimal traffic, costs should remain within Google Cloud's free tier.

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