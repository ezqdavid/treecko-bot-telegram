"""Tests for the bot module."""

import os
import tempfile
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from treecko_bot.bot import TreeckoBot
from treecko_bot.config import Config


@pytest.fixture
def config():
    """Create a test configuration."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    cfg = Config(
        telegram_token="test_token",
        google_credentials_path="credentials.json",
        google_sheet_id="",
        database_path=db_path,
        webhook_base_url="",
        port=8080,
    )
    yield cfg
    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.fixture
def bot(config):
    """Create a TreeckoBot instance with test config."""
    return TreeckoBot(config)


@pytest.fixture
def mock_update():
    """Create a mock Update object."""
    update = MagicMock()
    update.message = MagicMock()
    update.message.reply_text = AsyncMock()
    return update


@pytest.fixture
def mock_context():
    """Create a mock Context object."""
    return MagicMock()


class TestTreeckoBotCommands:
    """Tests for TreeckoBot command handlers."""

    @pytest.mark.asyncio
    async def test_start_command(self, bot, mock_update, mock_context):
        """Test the /start command handler."""
        await bot.start(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        assert "Welcome to Treecko Finance Bot" in call_args[0][0]
        assert call_args[1]["parse_mode"] == "Markdown"

    @pytest.mark.asyncio
    async def test_help_command(self, bot, mock_update, mock_context):
        """Test the /help command handler."""
        await bot.help_command(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        assert "Help" in call_args[0][0]
        assert "/start" in call_args[0][0]
        assert call_args[1]["parse_mode"] == "Markdown"

    @pytest.mark.asyncio
    async def test_status_command(self, bot, mock_update, mock_context):
        """Test the /status command handler."""
        await bot.status(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        assert "Status" in call_args[0][0]
        assert "Database" in call_args[0][0]
        assert call_args[1]["parse_mode"] == "Markdown"

    @pytest.mark.asyncio
    async def test_handle_text_message(self, bot, mock_update, mock_context):
        """Test handling a text message."""
        mock_update.message.text = "Hello bot"

        await bot.handle_text(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        assert "Hello bot" in call_args[0][0]


class TestTreeckoBotDocumentHandler:
    """Tests for TreeckoBot document handling."""

    @pytest.mark.asyncio
    async def test_handle_non_pdf_document(self, bot, mock_update, mock_context):
        """Test handling a non-PDF document."""
        mock_update.message.document = MagicMock()
        mock_update.message.document.file_name = "test.txt"

        await bot.handle_document(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        assert "PDF" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_handle_pdf_too_large(self, bot, mock_update, mock_context):
        """Test handling a PDF that exceeds the size limit."""
        mock_update.message.document = MagicMock()
        mock_update.message.document.file_name = "test.pdf"
        mock_update.message.document.file_size = 20 * 1024 * 1024  # 20 MB (over 10 MB limit)

        await bot.handle_document(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        assert "too large" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_handle_invalid_pdf_content(self, bot, mock_update, mock_context):
        """Test handling a file that is not a valid PDF despite extension."""
        mock_update.message.document = MagicMock()
        mock_update.message.document.file_name = "test.pdf"
        mock_update.message.document.file_id = "test_file_id"
        mock_update.message.document.file_size = 1024  # Small file

        # Mock file download with non-PDF content (doesn't start with %PDF)
        mock_file = AsyncMock()
        mock_file.download_as_bytearray = AsyncMock(return_value=bytearray(b"not a pdf content"))
        mock_context.bot = MagicMock()
        mock_context.bot.get_file = AsyncMock(return_value=mock_file)

        await bot.handle_document(mock_update, mock_context)

        # Should show error message about invalid PDF
        last_call = mock_update.message.reply_text.call_args
        assert "Invalid PDF" in last_call[0][0]

    @pytest.mark.asyncio
    async def test_handle_pdf_document_success(self, bot, mock_update, mock_context):
        """Test handling a valid PDF document."""
        mock_update.message.document = MagicMock()
        mock_update.message.document.file_name = "test.pdf"
        mock_update.message.document.file_id = "test_file_id"
        mock_update.message.document.file_size = 1024  # Small file

        # Mock file download with valid PDF magic bytes
        mock_file = AsyncMock()
        mock_file.download_as_bytearray = AsyncMock(
            return_value=bytearray(b"%PDF-1.4 mock pdf content")
        )
        mock_context.bot = MagicMock()
        mock_context.bot.get_file = AsyncMock(return_value=mock_file)

        # Mock PDF parser
        from datetime import datetime

        from treecko_bot.pdf_parser import ParsedTransaction

        mock_transaction = ParsedTransaction(
            transaction_id="TEST123",
            date=datetime(2024, 11, 15),
            description="Test transaction",
            amount=100.50,
            transaction_type="expense",
            merchant="Test Merchant",
            raw_text="test raw text",
        )

        with patch.object(bot.pdf_parser, "parse_from_bytes", return_value=mock_transaction):
            await bot.handle_document(mock_update, mock_context)

        # Should have called reply_text multiple times (downloading, analyzing, result)
        assert mock_update.message.reply_text.call_count >= 2

    @pytest.mark.asyncio
    async def test_handle_pdf_document_error(self, bot, mock_update, mock_context):
        """Test handling a PDF document that fails to parse."""
        mock_update.message.document = MagicMock()
        mock_update.message.document.file_name = "test.pdf"
        mock_update.message.document.file_id = "test_file_id"
        mock_update.message.document.file_size = 1024  # Small file

        # Mock file download with valid PDF magic bytes
        mock_file = AsyncMock()
        mock_file.download_as_bytearray = AsyncMock(
            return_value=bytearray(b"%PDF-1.4 mock pdf content")
        )
        mock_context.bot = MagicMock()
        mock_context.bot.get_file = AsyncMock(return_value=mock_file)

        # Mock PDF parser to raise an error
        with patch.object(
            bot.pdf_parser, "parse_from_bytes", side_effect=ValueError("Parse error")
        ):
            await bot.handle_document(mock_update, mock_context)

        # Should show error message
        last_call = mock_update.message.reply_text.call_args
        assert "Error" in last_call[0][0]


class TestTreeckoBotApplication:
    """Tests for TreeckoBot application creation."""

    def test_create_application(self, bot):
        """Test creating the Telegram application."""
        app = bot.create_application()

        # Check that handlers are registered
        assert app is not None
        # Application should have handlers
        assert len(app.handlers) > 0
