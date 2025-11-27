"""Tests for the PDF parser module."""

from datetime import datetime

import pytest

from treecko_bot.pdf_parser import MercadoPagoPDFParser


@pytest.fixture
def parser():
    """Create a parser instance."""
    return MercadoPagoPDFParser()


def test_parse_spanish_date(parser):
    """Test parsing Spanish format dates."""
    text = "15 de noviembre de 2024"
    tx = parser._parse_text(text)
    assert tx.date.year == 2024
    assert tx.date.month == 11
    assert tx.date.day == 15


def test_parse_numeric_date(parser):
    """Test parsing numeric format dates."""
    text = "Fecha: 15/11/2024"
    tx = parser._parse_text(text)
    assert tx.date.year == 2024
    assert tx.date.month == 11
    assert tx.date.day == 15


def test_extract_amount(parser):
    """Test extracting amount from text."""
    text = "Total: $1.500,50"
    tx = parser._parse_text(text)
    assert tx.amount == 1500.50


def test_extract_transaction_id(parser):
    """Test extracting transaction ID from text."""
    text = "Operación: 12345678901234"
    tx = parser._parse_text(text)
    assert tx.transaction_id == "12345678901234"


def test_determine_expense_type(parser):
    """Test determining transaction type for expenses."""
    text = "Pagaste $100.00"
    tx = parser._parse_text(text)
    assert tx.transaction_type == "expense"


def test_determine_income_type(parser):
    """Test determining transaction type for income."""
    text = "Recibiste $100.00"
    tx = parser._parse_text(text)
    assert tx.transaction_type == "income"


def test_extract_description(parser):
    """Test extracting description from text."""
    text = "Detalle: Compra en tienda online"
    tx = parser._parse_text(text)
    assert "Compra en tienda online" in tx.description


def test_extract_merchant(parser):
    """Test extracting merchant from text."""
    text = "Vendedor: Mi Tienda Favorita"
    tx = parser._parse_text(text)
    assert tx.merchant is not None
    assert "Mi Tienda" in tx.merchant
