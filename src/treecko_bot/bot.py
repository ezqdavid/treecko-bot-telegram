"""Telegram bot handlers."""

import logging
import os
import tempfile

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from .config import Config
from .database import DatabaseManager
from .pdf_parser import MercadoPagoPDFParser
from .sheets import GoogleSheetsManager

logger = logging.getLogger(__name__)


class TreeckoBot:
    """Telegram bot for personal finance management."""

    def __init__(self, config: Config):
        """Initialize the bot.

        Args:
            config: Bot configuration.
        """
        self.config = config
        self.db = DatabaseManager(config.database_path)
        self.pdf_parser = MercadoPagoPDFParser()
        self.sheets: GoogleSheetsManager | None = None

        if config.google_sheet_id and config.google_credentials_path:
            if os.path.exists(config.google_credentials_path):
                self.sheets = GoogleSheetsManager(
                    config.google_credentials_path, config.google_sheet_id
                )
            else:
                logger.warning(
                    f"Google credentials file not found: {config.google_credentials_path}"
                )

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle the /start command.

        Args:
            update: Telegram update object.
            context: Telegram context object.
        """
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
            "/status - Check bot status\n\n"
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
        help_text = (
            "🌿 *Treecko Finance Bot Help*\n\n"
            "*How to use:*\n"
            "1. Download your transaction receipt from MercadoPago as PDF\n"
            "2. Send the PDF to this chat\n"
            "3. I'll process it and store the transaction\n\n"
            "*Commands:*\n"
            "/start - Welcome message\n"
            "/help - This help message\n"
            "/status - Check configuration status\n\n"
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

    async def handle_document(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle document uploads (PDFs).

        Args:
            update: Telegram update object.
            context: Telegram context object.
        """
        document = update.message.document

        if not document.file_name.lower().endswith(".pdf"):
            await update.message.reply_text(
                "⚠️ Please send a PDF file. I can only process PDF documents."
            )
            return

        await update.message.reply_text("📥 Downloading PDF...")

        try:
            file = await context.bot.get_file(document.file_id)
            pdf_bytes = await file.download_as_bytearray()

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
                sheets_status = "✅ Added to Google Sheets" if success else "⚠️ Failed to add to Google Sheets"
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

    def create_application(self) -> Application:
        """Create and configure the Telegram application.

        Returns:
            Configured Application instance.
        """
        application = Application.builder().token(self.config.telegram_token).build()

        application.add_handler(CommandHandler("start", self.start))
        application.add_handler(CommandHandler("help", self.help_command))
        application.add_handler(CommandHandler("status", self.status))

        application.add_handler(
            MessageHandler(filters.Document.ALL, self.handle_document)
        )

        return application

    def run(self) -> None:
        """Run the bot."""
        logger.info("Starting Treecko Finance Bot...")
        application = self.create_application()
        application.run_polling(allowed_updates=Update.ALL_TYPES)
