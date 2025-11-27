"""Google Sheets integration for storing transactions."""

import logging
from datetime import datetime

import gspread
from google.oauth2.service_account import Credentials

logger = logging.getLogger(__name__)

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


class GoogleSheetsManager:
    """Manager for Google Sheets operations."""

    def __init__(self, credentials_path: str, sheet_id: str):
        """Initialize the Google Sheets manager.

        Args:
            credentials_path: Path to the Google service account credentials JSON file.
            sheet_id: The Google Sheets document ID.
        """
        self.credentials_path = credentials_path
        self.sheet_id = sheet_id
        self._client = None
        self._sheet = None

    def _get_client(self) -> gspread.Client:
        """Get or create the gspread client.

        Returns:
            Authenticated gspread client.
        """
        if self._client is None:
            credentials = Credentials.from_service_account_file(
                self.credentials_path, scopes=SCOPES
            )
            self._client = gspread.authorize(credentials)
        return self._client

    def _get_sheet(self) -> gspread.Spreadsheet:
        """Get the spreadsheet.

        Returns:
            The gspread Spreadsheet object.
        """
        if self._sheet is None:
            client = self._get_client()
            self._sheet = client.open_by_key(self.sheet_id)
        return self._sheet

    def _get_or_create_worksheet(self, title: str = "Transactions") -> gspread.Worksheet:
        """Get or create a worksheet.

        Args:
            title: The worksheet title.

        Returns:
            The gspread Worksheet object.
        """
        sheet = self._get_sheet()
        try:
            worksheet = sheet.worksheet(title)
        except gspread.WorksheetNotFound:
            worksheet = sheet.add_worksheet(title=title, rows=1000, cols=10)
            headers = [
                "Date",
                "Description",
                "Amount",
                "Type",
                "Merchant",
                "Category",
                "Transaction ID",
                "Created At",
            ]
            worksheet.update("A1:H1", [headers])
            worksheet.format("A1:H1", {"textFormat": {"bold": True}})
        return worksheet

    def add_transaction(
        self,
        date: datetime,
        description: str,
        amount: float,
        transaction_type: str,
        merchant: str | None = None,
        category: str | None = None,
        transaction_id: str | None = None,
    ) -> bool:
        """Add a transaction to the Google Sheet.

        Args:
            date: Transaction date.
            description: Transaction description.
            amount: Transaction amount.
            transaction_type: Type of transaction (income/expense).
            merchant: Optional merchant name.
            category: Optional category.
            transaction_id: Optional transaction ID.

        Returns:
            True if successful, False otherwise.
        """
        try:
            worksheet = self._get_or_create_worksheet()

            row = [
                date.strftime("%Y-%m-%d %H:%M:%S"),
                description,
                amount,
                transaction_type,
                merchant or "",
                category or "",
                transaction_id or "",
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            ]

            worksheet.append_row(row)
            logger.info(f"Added transaction to Google Sheets: {description}")
            return True
        except Exception as e:
            logger.error(f"Failed to add transaction to Google Sheets: {e}")
            return False

    def is_configured(self) -> bool:
        """Check if Google Sheets is properly configured.

        Returns:
            True if configured, False otherwise.
        """
        return bool(self.sheet_id) and bool(self.credentials_path)
