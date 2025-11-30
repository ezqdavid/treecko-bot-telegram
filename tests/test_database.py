"""Tests for the database module."""

import os
import tempfile
from datetime import datetime

import pytest
import pytest_asyncio

from treecko_bot.database import AsyncDatabaseManager, DatabaseManager


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


class TestAsyncDatabaseManager:
    """Tests for the async database manager."""

    @pytest_asyncio.fixture
    async def async_db(self):
        """Create a temporary async database for testing."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        manager = AsyncDatabaseManager(db_path)
        await manager.initialize()
        yield manager
        await manager.close()
        os.unlink(db_path)

    @pytest.mark.asyncio
    async def test_add_transaction(self, async_db):
        """Test adding a transaction asynchronously."""
        tx = await async_db.add_transaction(
            date=datetime(2024, 11, 15),
            description="Async Test transaction",
            amount=150.75,
            transaction_id="ASYNC123",
            transaction_type="expense",
            merchant="Async Test Merchant",
        )

        assert tx.id is not None
        assert tx.description == "Async Test transaction"
        assert tx.amount == 150.75
        assert tx.transaction_id == "ASYNC123"

    @pytest.mark.asyncio
    async def test_transaction_exists(self, async_db):
        """Test checking if a transaction exists asynchronously."""
        await async_db.add_transaction(
            date=datetime(2024, 11, 15),
            description="Async Test transaction",
            amount=100.50,
            transaction_id="ASYNCUNIQUE123",
        )

        assert await async_db.transaction_exists("ASYNCUNIQUE123")
        assert not await async_db.transaction_exists("NONEXISTENT")

    @pytest.mark.asyncio
    async def test_get_transaction_by_id(self, async_db):
        """Test retrieving a transaction by ID asynchronously."""
        await async_db.add_transaction(
            date=datetime(2024, 11, 15),
            description="Async Test transaction",
            amount=100.50,
            transaction_id="ASYNCFINDME123",
        )

        tx = await async_db.get_transaction_by_id("ASYNCFINDME123")
        assert tx is not None
        assert tx.transaction_id == "ASYNCFINDME123"

        tx_none = await async_db.get_transaction_by_id("NOTFOUND")
        assert tx_none is None

    @pytest.mark.asyncio
    async def test_get_all_transactions(self, async_db):
        """Test retrieving all transactions asynchronously."""
        await async_db.add_transaction(
            date=datetime(2024, 11, 15),
            description="Async Transaction 1",
            amount=100.00,
        )
        await async_db.add_transaction(
            date=datetime(2024, 11, 16),
            description="Async Transaction 2",
            amount=200.00,
        )

        all_tx = await async_db.get_all_transactions()
        assert len(all_tx) == 2

    @pytest.mark.asyncio
    async def test_initialize_is_idempotent(self, async_db):
        """Test that initialize can be called multiple times safely."""
        # Initialize was already called in fixture
        await async_db.initialize()  # Should not raise
        await async_db.initialize()  # Should not raise

        # Verify database still works
        tx = await async_db.add_transaction(
            date=datetime(2024, 11, 15),
            description="After multiple inits",
            amount=50.00,
        )
        assert tx.id is not None
