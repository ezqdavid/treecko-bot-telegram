"""PDF parser for MercadoPago transaction receipts."""

import io
import re
from dataclasses import dataclass
from datetime import datetime

import pdfplumber


@dataclass
class ParsedTransaction:
    """Parsed transaction data from a MercadoPago PDF."""

    transaction_id: str | None
    date: datetime
    description: str
    amount: float
    transaction_type: str  # "income" or "expense"
    merchant: str | None
    raw_text: str


class MercadoPagoPDFParser:
    """Parser for MercadoPago PDF receipts."""

    def parse(self, pdf_path: str) -> ParsedTransaction:
        """Parse a MercadoPago PDF receipt.

        Args:
            pdf_path: Path to the PDF file.

        Returns:
            ParsedTransaction object with extracted data.

        Raises:
            ValueError: If the PDF cannot be parsed.
        """
        with pdfplumber.open(pdf_path) as pdf:
            text = ""
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"

        if not text.strip():
            raise ValueError("Could not extract text from PDF")

        return self._parse_text(text)

    def parse_from_bytes(self, pdf_bytes: bytes) -> ParsedTransaction:
        """Parse a MercadoPago PDF from bytes.

        Args:
            pdf_bytes: PDF file content as bytes.

        Returns:
            ParsedTransaction object with extracted data.

        Raises:
            ValueError: If the PDF cannot be parsed.
        """
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            text = ""
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"

        if not text.strip():
            raise ValueError("Could not extract text from PDF")

        return self._parse_text(text)

    def _parse_text(self, text: str) -> ParsedTransaction:
        """Parse the extracted text from a MercadoPago receipt.

        Args:
            text: Extracted text from the PDF.

        Returns:
            ParsedTransaction object with extracted data.
        """
        transaction_id = self._extract_transaction_id(text)
        date = self._extract_date(text)
        amount, transaction_type = self._extract_amount(text)
        description = self._extract_description(text)
        merchant = self._extract_merchant(text)

        return ParsedTransaction(
            transaction_id=transaction_id,
            date=date,
            description=description,
            amount=amount,
            transaction_type=transaction_type,
            merchant=merchant,
            raw_text=text,
        )

    def _extract_transaction_id(self, text: str) -> str | None:
        """Extract transaction ID from the text.

        Args:
            text: PDF text content.

        Returns:
            Transaction ID if found, None otherwise.
        """
        patterns = [
            r"(?:Operación|Operacion|ID|Código|Codigo)[\s:]*[#]?(\d{10,})",
            r"(?:N[úu]mero de operaci[óo]n)[\s:]*(\d+)",
            r"(?:Comprobante|Referencia)[\s:]*(\d{8,})",
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)

        return None

    def _extract_date(self, text: str) -> datetime:
        """Extract transaction date from the text.

        Args:
            text: PDF text content.

        Returns:
            Datetime object of the transaction date.
        """
        date_patterns = [
            (r"(\d{1,2})\s+de\s+(\w+)\s+de\s+(\d{4})", self._parse_spanish_date),
            (r"(\d{1,2})/(\d{1,2})/(\d{4})", self._parse_numeric_date),
            (r"(\d{1,2})-(\d{1,2})-(\d{4})", self._parse_numeric_date_dash),
            (r"(\d{4})-(\d{1,2})-(\d{1,2})", self._parse_iso_date),
        ]

        for pattern, parser in date_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    return parser(match)
                except (ValueError, KeyError):
                    continue

        return datetime.now()

    def _parse_spanish_date(self, match: re.Match) -> datetime:
        """Parse a Spanish format date (e.g., '15 de noviembre de 2024').

        Args:
            match: Regex match object.

        Returns:
            Datetime object.
        """
        months = {
            "enero": 1,
            "febrero": 2,
            "marzo": 3,
            "abril": 4,
            "mayo": 5,
            "junio": 6,
            "julio": 7,
            "agosto": 8,
            "septiembre": 9,
            "octubre": 10,
            "noviembre": 11,
            "diciembre": 12,
        }
        day = int(match.group(1))
        month_name = match.group(2).lower()
        year = int(match.group(3))
        month = months[month_name]
        return datetime(year, month, day)

    def _parse_numeric_date(self, match: re.Match) -> datetime:
        """Parse a numeric date (e.g., '15/11/2024').

        Args:
            match: Regex match object.

        Returns:
            Datetime object.
        """
        day = int(match.group(1))
        month = int(match.group(2))
        year = int(match.group(3))
        return datetime(year, month, day)

    def _parse_numeric_date_dash(self, match: re.Match) -> datetime:
        """Parse a numeric date with dashes (e.g., '15-11-2024').

        Args:
            match: Regex match object.

        Returns:
            Datetime object.
        """
        day = int(match.group(1))
        month = int(match.group(2))
        year = int(match.group(3))
        return datetime(year, month, day)

    def _parse_iso_date(self, match: re.Match) -> datetime:
        """Parse an ISO format date (e.g., '2024-11-15').

        Args:
            match: Regex match object.

        Returns:
            Datetime object.
        """
        year = int(match.group(1))
        month = int(match.group(2))
        day = int(match.group(3))
        return datetime(year, month, day)

    def _extract_amount(self, text: str) -> tuple[float, str]:
        """Extract transaction amount from the text.

        Args:
            text: PDF text content.

        Returns:
            Tuple of (amount, transaction_type).
        """
        amount_patterns = [
            r"\$\s*([\d.,]+)",
            r"(?:Total|Monto|Importe)[\s:]*\$?\s*([\d.,]+)",
            r"([\d.,]+)\s*(?:pesos|ARS)",
        ]

        for pattern in amount_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                amount_str = match.group(1).replace(".", "").replace(",", ".")
                try:
                    amount = float(amount_str)
                    transaction_type = self._determine_transaction_type(text)
                    return (amount, transaction_type)
                except ValueError:
                    continue

        return (0.0, "expense")

    def _determine_transaction_type(self, text: str) -> str:
        """Determine if the transaction is income or expense.

        Args:
            text: PDF text content.

        Returns:
            'income' or 'expense'.
        """
        income_keywords = ["recibiste", "cobraste", "ingreso", "depósito", "deposito"]
        expense_keywords = ["pagaste", "enviaste", "compra", "pago", "transferencia"]

        text_lower = text.lower()

        for keyword in income_keywords:
            if keyword in text_lower:
                return "income"

        for keyword in expense_keywords:
            if keyword in text_lower:
                return "expense"

        return "expense"

    def _extract_description(self, text: str) -> str:
        """Extract transaction description from the text.

        Args:
            text: PDF text content.

        Returns:
            Transaction description.
        """
        description_patterns = [
            r"(?:Detalle|Descripción|Descripcion|Concepto)[\s:]*(.+?)(?:\n|$)",
            r"(?:por|Para)[\s:]*(.+?)(?:\n|$)",
        ]

        for pattern in description_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                description = match.group(1).strip()
                if description and len(description) > 3:
                    return description[:200]

        lines = [line.strip() for line in text.split("\n") if line.strip()]
        if len(lines) > 2:
            return lines[1][:200]

        return "MercadoPago Transaction"

    def _extract_merchant(self, text: str) -> str | None:
        """Extract merchant name from the text.

        Args:
            text: PDF text content.

        Returns:
            Merchant name if found, None otherwise.
        """
        merchant_patterns = [
            r"(?:Vendedor|Comercio|Destinatario|Para|A)[\s:]*(.+?)(?:\n|$)",
            r"(?:De|Remitente)[\s:]*(.+?)(?:\n|$)",
        ]

        for pattern in merchant_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                merchant = match.group(1).strip()
                if merchant and len(merchant) > 2:
                    return merchant[:100]

        return None
