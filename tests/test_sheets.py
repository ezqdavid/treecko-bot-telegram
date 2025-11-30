"""Tests for the sheets module."""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from treecko_bot.sheets import GoogleSheetsManager


@pytest.fixture
def sheets_manager():
    """Create a GoogleSheetsManager instance with test credentials."""
    return GoogleSheetsManager(
        credentials_path="test_credentials.json",
        sheet_id="test_sheet_id"
    )


class TestGoogleSheetsManagerConfiguration:
    """Tests for GoogleSheetsManager configuration."""

    def test_is_configured_returns_true_when_configured(self, sheets_manager):
        """Test is_configured returns True when both credentials_path and sheet_id are set."""
        assert sheets_manager.is_configured() is True

    def test_is_configured_returns_false_when_no_sheet_id(self):
        """Test is_configured returns False when sheet_id is empty."""
        manager = GoogleSheetsManager(
            credentials_path="test_credentials.json",
            sheet_id=""
        )
        assert manager.is_configured() is False

    def test_is_configured_returns_false_when_no_credentials_path(self):
        """Test is_configured returns False when credentials_path is empty."""
        manager = GoogleSheetsManager(
            credentials_path="",
            sheet_id="test_sheet_id"
        )
        assert manager.is_configured() is False

    def test_initialization_stores_credentials_path(self, sheets_manager):
        """Test that initialization stores credentials path."""
        assert sheets_manager.credentials_path == "test_credentials.json"

    def test_initialization_stores_sheet_id(self, sheets_manager):
        """Test that initialization stores sheet ID."""
        assert sheets_manager.sheet_id == "test_sheet_id"


class TestGoogleSheetsManagerAddTransaction:
    """Tests for GoogleSheetsManager.add_transaction method."""

    def test_add_transaction_success(self, sheets_manager):
        """Test adding a transaction successfully."""
        mock_worksheet = MagicMock()
        mock_worksheet.append_row = MagicMock()

        with patch.object(
            sheets_manager, "_get_or_create_worksheet", return_value=mock_worksheet
        ):
            result = sheets_manager.add_transaction(
                date=datetime(2024, 11, 15, 10, 30, 0),
                description="Test transaction",
                amount=100.50,
                transaction_type="expense",
                merchant="Test Merchant",
                category="Shopping",
                transaction_id="TX123",
            )

        assert result is True
        mock_worksheet.append_row.assert_called_once()
        row_data = mock_worksheet.append_row.call_args[0][0]
        assert row_data[0] == "2024-11-15 10:30:00"  # date
        assert row_data[1] == "Test transaction"  # description
        assert row_data[2] == 100.50  # amount
        assert row_data[3] == "expense"  # transaction_type
        assert row_data[4] == "Test Merchant"  # merchant
        assert row_data[5] == "Shopping"  # category
        assert row_data[6] == "TX123"  # transaction_id

    def test_add_transaction_with_optional_fields_empty(self, sheets_manager):
        """Test adding a transaction with optional fields empty."""
        mock_worksheet = MagicMock()
        mock_worksheet.append_row = MagicMock()

        with patch.object(
            sheets_manager, "_get_or_create_worksheet", return_value=mock_worksheet
        ):
            result = sheets_manager.add_transaction(
                date=datetime(2024, 11, 15),
                description="Test transaction",
                amount=50.00,
                transaction_type="income",
            )

        assert result is True
        row_data = mock_worksheet.append_row.call_args[0][0]
        assert row_data[4] == ""  # merchant should be empty string
        assert row_data[5] == ""  # category should be empty string
        assert row_data[6] == ""  # transaction_id should be empty string

    def test_add_transaction_failure(self, sheets_manager):
        """Test handling failure when adding a transaction."""
        with patch.object(
            sheets_manager,
            "_get_or_create_worksheet",
            side_effect=Exception("Connection error"),
        ):
            result = sheets_manager.add_transaction(
                date=datetime(2024, 11, 15),
                description="Test transaction",
                amount=100.50,
                transaction_type="expense",
            )

        assert result is False


class TestGoogleSheetsManagerClientAndSheet:
    """Tests for GoogleSheetsManager client and sheet methods."""

    def test_get_client_creates_client_once(self, sheets_manager):
        """Test that _get_client creates and caches the client."""
        mock_credentials = MagicMock()
        mock_client = MagicMock()

        with patch(
            "treecko_bot.sheets.Credentials.from_service_account_file",
            return_value=mock_credentials
        ) as mock_creds:
            with patch("treecko_bot.sheets.gspread.authorize", return_value=mock_client):
                # First call should create client
                client1 = sheets_manager._get_client()
                # Second call should return cached client
                client2 = sheets_manager._get_client()

        assert client1 is client2
        mock_creds.assert_called_once()  # Should only be called once due to caching

    def test_get_sheet_opens_by_key(self, sheets_manager):
        """Test that _get_sheet opens the spreadsheet by key."""
        mock_client = MagicMock()
        mock_spreadsheet = MagicMock()
        mock_client.open_by_key = MagicMock(return_value=mock_spreadsheet)

        with patch.object(sheets_manager, "_get_client", return_value=mock_client):
            sheet = sheets_manager._get_sheet()

        assert sheet is mock_spreadsheet
        mock_client.open_by_key.assert_called_once_with("test_sheet_id")

    def test_get_or_create_worksheet_existing(self, sheets_manager):
        """Test getting an existing worksheet."""
        mock_sheet = MagicMock()
        mock_worksheet = MagicMock()
        mock_sheet.worksheet = MagicMock(return_value=mock_worksheet)

        with patch.object(sheets_manager, "_get_sheet", return_value=mock_sheet):
            worksheet = sheets_manager._get_or_create_worksheet("Transactions")

        assert worksheet is mock_worksheet
        mock_sheet.worksheet.assert_called_once_with("Transactions")

    def test_get_or_create_worksheet_creates_new(self, sheets_manager):
        """Test creating a new worksheet when it doesn't exist."""
        import gspread

        mock_sheet = MagicMock()
        mock_new_worksheet = MagicMock()
        mock_sheet.worksheet = MagicMock(side_effect=gspread.WorksheetNotFound("Not found"))
        mock_sheet.add_worksheet = MagicMock(return_value=mock_new_worksheet)

        with patch.object(sheets_manager, "_get_sheet", return_value=mock_sheet):
            worksheet = sheets_manager._get_or_create_worksheet("NewSheet")

        assert worksheet is mock_new_worksheet
        mock_sheet.add_worksheet.assert_called_once()
        mock_new_worksheet.update.assert_called_once()  # Headers should be added
        mock_new_worksheet.format.assert_called_once()  # Headers should be formatted
