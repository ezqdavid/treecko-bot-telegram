"""Telegram bot handlers."""

import csv
import hashlib
import io
import os
import time
from datetime import datetime, timedelta

from telegram import InputFile, Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from .authorization import UserAuthorization
from .config import Config
from .database import DatabaseManager
from .health import HealthCheckServer, HealthStatus
from .logging_config import get_logger
from .pdf_parser import MercadoPagoPDFParser
from .rate_limiter import RateLimiter
from .sheets import GoogleSheetsManager

logger = get_logger(__name__)

# Default host for webhook server
WEBHOOK_HOST = "0.0.0.0"

# PDF validation constants
MAX_PDF_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB max file size
PDF_MAGIC_BYTES = b"%PDF"  # PDF files start with this signature


class TreeckoBot:
    """Telegram bot for personal finance management."""

    def __init__(self, config: Config) -> None:
        """Initialize the bot.

        Args:
            config: Bot configuration.
        """
        self.config = config
        self.db = DatabaseManager(config.database_path)
        self.pdf_parser = MercadoPagoPDFParser()
        self.sheets: GoogleSheetsManager | None = None
        self._health_server: HealthCheckServer | None = None
        self.rate_limiter = RateLimiter(config.rate_limit_config)
        self.authorization = UserAuthorization(config.auth_config)

        if config.google_sheet_id and config.google_credentials_path:
            if os.path.exists(config.google_credentials_path):
                self.sheets = GoogleSheetsManager(
                    config.google_credentials_path, config.google_sheet_id
                )
            else:
                logger.warning(
                    f"Google credentials file not found: {config.google_credentials_path}"
                )

    def _get_health_status(self) -> HealthStatus:
        """Get current health status for health check endpoint.

        Returns:
            HealthStatus object with current status.
        """
        return HealthStatus(
            status="healthy",
            timestamp=time.time(),
            database_connected=self.db is not None,
            sheets_configured=self.sheets is not None and self.sheets.is_configured(),
        )

    async def _check_access(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> bool:
        """Check authorization and rate limiting for a request.

        Args:
            update: Telegram update object.
            context: Telegram context object.

        Returns:
            True if access is granted, False otherwise.
        """
        if not update.effective_user:
            return False

        user_id = update.effective_user.id

        # Check authorization
        if not self.authorization.is_authorized(user_id):
            message = self.authorization.get_unauthorized_message()
            if update.message:
                await update.message.reply_text(message, parse_mode="Markdown")
            logger.warning("Unauthorized access attempt", user_id=user_id)
            return False

        # Check rate limiting
        if not self.rate_limiter.check_and_record(user_id):
            retry_after = self.rate_limiter.get_retry_after(user_id)
            message = (
                "⏳ *Rate Limited*\n\n"
                f"You're making requests too quickly.\n"
                f"Please wait {int(retry_after)} seconds before trying again."
            )
            if update.message:
                await update.message.reply_text(message, parse_mode="Markdown")
            return False

        return True

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle the /start command.

        Args:
            update: Telegram update object.
            context: Telegram context object.
        """
        if not await self._check_access(update, context):
            return

        welcome_message = (
            "🌿 *Welcome to Treecko Finance Bot!*\n\n"
            "I'm your personal finance assistant. Here's what I can do:\n\n"
            "📄 *Process MercadoPago PDFs*\n"
            "Send me a PDF receipt from MercadoPago and I'll:\n"
            "• Extract the transaction details\n"
            "• Store it in the database\n"
            "• Add it to your Google Sheets report\n\n"
            "📊 *Commands*\n"
            "/start - Show this welcome message\n"
            "/help - Get help\n"
            "/status - Check bot status\n"
            "/report - View transaction summary\n"
            "/export - Download transactions as CSV\n\n"
            "Just send me a PDF to get started! 📤"
        )
        await update.message.reply_text(welcome_message, parse_mode="Markdown")

    async def help_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle the /help command.

        Args:
            update: Telegram update object.
            context: Telegram context object.
        """
        if not await self._check_access(update, context):
            return

        help_text = (
            "🌿 *Treecko Finance Bot Help*\n\n"
            "*How to use:*\n"
            "1. Download your transaction receipt from MercadoPago as PDF\n"
            "2. Send the PDF to this chat\n"
            "3. I'll process it and store the transaction\n\n"
            "*Commands:*\n"
            "/start - Welcome message\n"
            "/help - This help message\n"
            "/status - Check configuration status\n"
            "/report - View transaction summary\n"
            "/export - Download transactions as CSV\n\n"
            "*Report Options:*\n"
            "`/report week` - Last 7 days\n"
            "`/report month` - Last 30 days (default)\n"
            "`/report year` - Last 365 days\n"
            "`/report all` - All time\n\n"
            "*Tips:*\n"
            "• Make sure the PDF is readable\n"
            "• One PDF per message works best\n"
            "• Transactions are automatically categorized"
        )
        await update.message.reply_text(help_text, parse_mode="Markdown")

    async def status(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle the /status command.

        Args:
            update: Telegram update object.
            context: Telegram context object.
        """
        if not await self._check_access(update, context):
            return

        db_status = "✅ Connected" if self.db else "❌ Not configured"
        sheets_status = (
            "✅ Configured" if self.sheets and self.sheets.is_configured() else "⚠️ Not configured"
        )

        status_text = (
            "🌿 *Treecko Bot Status*\n\n"
            f"📦 *Database:* {db_status}\n"
            f"📊 *Google Sheets:* {sheets_status}\n"
        )
        await update.message.reply_text(status_text, parse_mode="Markdown")

    async def report(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle the /report command for transaction summaries.

        Args:
            update: Telegram update object.
            context: Telegram context object.
        """
        if not await self._check_access(update, context):
            return

        # Parse optional date range from arguments
        args = context.args or []
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)  # Default: last 30 days
        period_text = "last 30 days"

        if args:
            period = args[0].lower()
            if period == "week":
                start_date = end_date - timedelta(days=7)
                period_text = "last 7 days"
            elif period == "month":
                start_date = end_date - timedelta(days=30)
                period_text = "last 30 days"
            elif period == "year":
                start_date = end_date - timedelta(days=365)
                period_text = "last year"
            elif period == "all":
                start_date = None
                period_text = "all time"

        summary = self.db.get_transaction_summary(start_date, end_date)

        # Format amounts with signs
        income_str = f"+${summary['total_income']:,.2f}"
        expense_str = f"-${summary['total_expense']:,.2f}"
        net_sign = "+" if summary["net_balance"] >= 0 else ""
        net_str = f"{net_sign}${summary['net_balance']:,.2f}"

        report_text = (
            "📊 *Transaction Report*\n"
            f"📅 Period: {period_text}\n\n"
            f"💰 *Income:* {income_str} ({summary['income_count']} transactions)\n"
            f"💸 *Expenses:* {expense_str} ({summary['expense_count']} transactions)\n"
            f"📈 *Net Balance:* {net_str}\n\n"
            f"📝 *Total Transactions:* {summary['transaction_count']}\n\n"
            "_Use /report week, /report month, /report year, or /report all_"
        )
        await update.message.reply_text(report_text, parse_mode="Markdown")

    async def export(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle the /export command to download transactions as CSV.

        Args:
            update: Telegram update object.
            context: Telegram context object.
        """
        if not await self._check_access(update, context):
            return

        transactions = self.db.get_all_transactions()

        if not transactions:
            await update.message.reply_text(
                "📭 No transactions to export.\n"
                "Send me a MercadoPago PDF to get started!"
            )
            return

        # Create CSV in memory
        output = io.StringIO()
        writer = csv.writer(output)

        # Write header
        writer.writerow([
            "Date",
            "Description",
            "Amount",
            "Type",
            "Category",
            "Merchant",
            "Transaction ID",
            "Created At",
        ])

        # Write transactions
        for tx in transactions:
            writer.writerow([
                tx.date.strftime("%Y-%m-%d %H:%M:%S") if tx.date else "",
                tx.description or "",
                tx.amount,
                tx.transaction_type or "",
                tx.category or "",
                tx.merchant or "",
                tx.transaction_id or "",
                tx.created_at.strftime("%Y-%m-%d %H:%M:%S") if tx.created_at else "",
            ])

        # Send as file
        csv_bytes = output.getvalue().encode("utf-8")
        csv_file = io.BytesIO(csv_bytes)
        csv_file.name = f"transactions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

        await update.message.reply_document(
            document=InputFile(csv_file, filename=csv_file.name),
            caption=f"📥 *Exported {len(transactions)} transactions*",
            parse_mode="Markdown",
        )

    async def handle_document(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle document uploads (PDFs).

        Args:
            update: Telegram update object.
            context: Telegram context object.
        """
        if not await self._check_access(update, context):
            return

        document = update.message.document

        if not document.file_name.lower().endswith(".pdf"):
            await update.message.reply_text(
                "⚠️ Please send a PDF file. I can only process PDF documents."
            )
            return

        # Validate file size before downloading
        if document.file_size and document.file_size > MAX_PDF_SIZE_BYTES:
            max_size_mb = MAX_PDF_SIZE_BYTES / (1024 * 1024)
            await update.message.reply_text(
                f"⚠️ File too large. Maximum allowed size is {max_size_mb:.0f} MB."
            )
            return

        await update.message.reply_text("📥 Downloading PDF...")

        try:
            file = await context.bot.get_file(document.file_id)
            pdf_bytes = await file.download_as_bytearray()

            # Validate PDF content (magic bytes check)
            if not bytes(pdf_bytes[:4]).startswith(PDF_MAGIC_BYTES):
                await update.message.reply_text(
                    "⚠️ Invalid PDF file. The file does not appear to be a valid PDF document."
                )
                return

            await update.message.reply_text("🔍 Analyzing transaction...")

            transaction = self.pdf_parser.parse_from_bytes(bytes(pdf_bytes))

            if transaction.transaction_id and self.db.transaction_exists(
                transaction.transaction_id
            ):
                await update.message.reply_text(
                    "⚠️ This transaction has already been processed."
                )
                return

            db_transaction = self.db.add_transaction(
                date=transaction.date,
                description=transaction.description,
                amount=transaction.amount,
                transaction_id=transaction.transaction_id,
                transaction_type=transaction.transaction_type,
                merchant=transaction.merchant,
                raw_text=transaction.raw_text,
            )

            sheets_status = ""
            if self.sheets and self.sheets.is_configured():
                success = self.sheets.add_transaction(
                    date=transaction.date,
                    description=transaction.description,
                    amount=transaction.amount,
                    transaction_type=transaction.transaction_type,
                    merchant=transaction.merchant,
                    transaction_id=transaction.transaction_id,
                )
                if success:
                    sheets_status = "✅ Added to Google Sheets"
                else:
                    sheets_status = "⚠️ Failed to add to Google Sheets"
            else:
                sheets_status = "⚠️ Google Sheets not configured"

            amount_sign = "+" if transaction.transaction_type == "income" else "-"
            emoji = "💰" if transaction.transaction_type == "income" else "💸"

            response = (
                f"{emoji} *Transaction Processed!*\n\n"
                f"📅 *Date:* {transaction.date.strftime('%Y-%m-%d')}\n"
                f"📝 *Description:* {transaction.description}\n"
                f"💵 *Amount:* {amount_sign}${transaction.amount:,.2f}\n"
                f"🏷️ *Type:* {transaction.transaction_type.capitalize()}\n"
            )

            if transaction.merchant:
                response += f"🏪 *Merchant:* {transaction.merchant}\n"

            if transaction.transaction_id:
                response += f"🔢 *ID:* {transaction.transaction_id}\n"

            response += f"\n📦 *Database:* ✅ Stored (ID: {db_transaction.id})\n"
            response += f"📊 *Sheets:* {sheets_status}"

            await update.message.reply_text(response, parse_mode="Markdown")

        except Exception as e:
            logger.error(f"Error processing PDF: {e}", exc_info=True)
            await update.message.reply_text(
                f"❌ Error processing PDF: {str(e)}\n\n"
                "Please make sure this is a valid MercadoPago receipt."
            )

    async def handle_text(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle text messages.

        Args:
            update: Telegram update object.
            context: Telegram context object.
        """
        if not await self._check_access(update, context):
            return

        text = update.message.text
        response = (
            f"📝 Recibí tu mensaje: \"{text}\"\n\n"
            "Para procesar una transacción, envíame un PDF de MercadoPago.\n"
            "Usa /help para ver los comandos disponibles."
        )
        await update.message.reply_text(response)

    def create_application(self) -> Application:
        """Create and configure the Telegram application.

        Returns:
            Configured Application instance.
        """
        application = Application.builder().token(self.config.telegram_token).build()

        # Command handlers
        application.add_handler(CommandHandler("start", self.start))
        application.add_handler(CommandHandler("help", self.help_command))
        application.add_handler(CommandHandler("status", self.status))
        application.add_handler(CommandHandler("report", self.report))
        application.add_handler(CommandHandler("export", self.export))

        # Document handler for PDFs
        application.add_handler(
            MessageHandler(filters.Document.ALL, self.handle_document)
        )

        # Text message handler (excluding commands)
        application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_text)
        )

        return application

    def _start_health_server(self) -> None:
        """Start the health check server."""
        self._health_server = HealthCheckServer(
            port=self.config.health_check_port,
            health_callback=self._get_health_status,
        )
        self._health_server.start()

    def _stop_health_server(self) -> None:
        """Stop the health check server."""
        if self._health_server:
            self._health_server.stop()
            self._health_server = None

    def run(self) -> None:
        """Run the bot using webhook mode (if WEBHOOK_BASE_URL is set) or polling mode."""
        logger.info("Starting Treecko Finance Bot...")

        # Start health check server
        self._start_health_server()

        try:
            application = self.create_application()

            if self.config.webhook_base_url:
                self._run_webhook(application)
            else:
                self._run_polling(application)
        finally:
            self._stop_health_server()

    def _run_polling(self, application: Application) -> None:
        """Run the bot using long polling (for local development without tunnel).

        Args:
            application: The Telegram Application instance.
        """
        logger.info("Running bot in polling mode...")
        application.run_polling(allowed_updates=Update.ALL_TYPES)

    def _run_webhook(self, application: Application) -> None:
        """Run the bot using webhook mode (for Cloud Run deployment).

        Args:
            application: The Telegram Application instance.
        """
        # Build webhook URL using a hash of the token for security
        # This prevents the full token from appearing in server logs
        token_hash = hashlib.sha256(self.config.telegram_token.encode()).hexdigest()[:16]
        webhook_path = f"/webhook/{token_hash}"
        webhook_url = f"{self.config.webhook_base_url}{webhook_path}"

        logger.info(f"Running bot in webhook mode on port {self.config.port}...")
        logger.info(f"Webhook path: /webhook/{token_hash}")

        application.run_webhook(
            listen=WEBHOOK_HOST,
            port=self.config.port,
            url_path=webhook_path,
            webhook_url=webhook_url,
            allowed_updates=Update.ALL_TYPES,
        )
