"""Tests for the database module."""

import os
import tempfile
from datetime import datetime

import pytest

from treecko_bot.database import DatabaseManager


@pytest.fixture
def db():
    """Create a temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    manager = DatabaseManager(db_path)
    yield manager
    os.unlink(db_path)


def test_add_transaction(db):
    """Test adding a transaction to the database."""
    tx = db.add_transaction(
        date=datetime(2024, 11, 15),
        description="Test transaction",
        amount=100.50,
        transaction_id="TEST123",
        transaction_type="expense",
        merchant="Test Merchant",
    )

    assert tx.id is not None
    assert tx.description == "Test transaction"
    assert tx.amount == 100.50
    assert tx.transaction_id == "TEST123"


def test_transaction_exists(db):
    """Test checking if a transaction exists."""
    db.add_transaction(
        date=datetime(2024, 11, 15),
        description="Test transaction",
        amount=100.50,
        transaction_id="UNIQUE123",
    )

    assert db.transaction_exists("UNIQUE123")
    assert not db.transaction_exists("NONEXISTENT")


def test_get_transaction_by_id(db):
    """Test retrieving a transaction by ID."""
    db.add_transaction(
        date=datetime(2024, 11, 15),
        description="Test transaction",
        amount=100.50,
        transaction_id="FINDME123",
    )

    tx = db.get_transaction_by_id("FINDME123")
    assert tx is not None
    assert tx.transaction_id == "FINDME123"

    tx_none = db.get_transaction_by_id("NOTFOUND")
    assert tx_none is None


def test_get_all_transactions(db):
    """Test retrieving all transactions."""
    db.add_transaction(
        date=datetime(2024, 11, 15),
        description="Transaction 1",
        amount=100.00,
    )
    db.add_transaction(
        date=datetime(2024, 11, 16),
        description="Transaction 2",
        amount=200.00,
    )

    all_tx = db.get_all_transactions()
    assert len(all_tx) == 2
