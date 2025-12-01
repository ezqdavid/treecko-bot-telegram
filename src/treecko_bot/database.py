"""SQLite database models and operations."""

from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Float, Integer, String, create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

Base = declarative_base()


def _utc_now() -> datetime:
    """Return current UTC time."""
    return datetime.now(timezone.utc)


class Transaction(Base):
    """Transaction model for storing MercadoPago transactions."""

    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    transaction_id = Column(String, unique=True, nullable=True)
    date = Column(DateTime, nullable=False)
    description = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    transaction_type = Column(String, nullable=True)  # income/expense
    category = Column(String, nullable=True)
    merchant = Column(String, nullable=True)
    raw_text = Column(String, nullable=True)
    created_at = Column(DateTime, default=_utc_now)


class DatabaseManager:
    """Manager class for database operations."""

    def __init__(self, database_path: str) -> None:
        """Initialize the database manager.

        Args:
            database_path: Path to the SQLite database file.
        """
        self.engine = create_engine(f"sqlite:///{database_path}")
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine)

    def get_session(self) -> Session:
        """Get a new database session."""
        return self.SessionLocal()

    def add_transaction(
        self,
        date: datetime,
        description: str,
        amount: float,
        transaction_id: str | None = None,
        transaction_type: str | None = None,
        category: str | None = None,
        merchant: str | None = None,
        raw_text: str | None = None,
    ) -> Transaction:
        """Add a new transaction to the database.

        Args:
            date: Transaction date.
            description: Transaction description.
            amount: Transaction amount.
            transaction_id: Optional unique transaction ID.
            transaction_type: Type of transaction (income/expense).
            category: Transaction category.
            merchant: Merchant name.
            raw_text: Raw text extracted from PDF.

        Returns:
            The created Transaction object.
        """
        with self.get_session() as session:
            transaction = Transaction(
                transaction_id=transaction_id,
                date=date,
                description=description,
                amount=amount,
                transaction_type=transaction_type,
                category=category,
                merchant=merchant,
                raw_text=raw_text,
            )
            session.add(transaction)
            session.commit()
            session.refresh(transaction)
            return transaction

    def get_transaction_by_id(self, transaction_id: str) -> Transaction | None:
        """Get a transaction by its transaction ID.

        Args:
            transaction_id: The transaction ID to search for.

        Returns:
            The Transaction if found, None otherwise.
        """
        with self.get_session() as session:
            return (
                session.query(Transaction)
                .filter(Transaction.transaction_id == transaction_id)
                .first()
            )

    def get_all_transactions(self) -> list[Transaction]:
        """Get all transactions from the database.

        Returns:
            List of all transactions.
        """
        with self.get_session() as session:
            return session.query(Transaction).all()

    def transaction_exists(self, transaction_id: str) -> bool:
        """Check if a transaction already exists.

        Args:
            transaction_id: The transaction ID to check.

        Returns:
            True if transaction exists, False otherwise.
        """
        return self.get_transaction_by_id(transaction_id) is not None


class AsyncDatabaseManager:
    """Async manager class for database operations.

    Uses async SQLAlchemy with aiosqlite for non-blocking database operations.
    This is preferred for use in async contexts like Telegram bot handlers.
    """

    def __init__(self, database_path: str) -> None:
        """Initialize the async database manager.

        Args:
            database_path: Path to the SQLite database file.
        """
        self.database_path = database_path
        self.engine = create_async_engine(
            f"sqlite+aiosqlite:///{database_path}",
            echo=False,
        )
        self.async_session = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize the database schema.

        Must be called before using other async methods.
        """
        if self._initialized:
            return

        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        self._initialized = True

    async def get_session(self) -> AsyncSession:
        """Get a new async database session."""
        return self.async_session()

    async def add_transaction(
        self,
        date: datetime,
        description: str,
        amount: float,
        transaction_id: str | None = None,
        transaction_type: str | None = None,
        category: str | None = None,
        merchant: str | None = None,
        raw_text: str | None = None,
    ) -> Transaction:
        """Add a new transaction to the database asynchronously.

        Args:
            date: Transaction date.
            description: Transaction description.
            amount: Transaction amount.
            transaction_id: Optional unique transaction ID.
            transaction_type: Type of transaction (income/expense).
            category: Transaction category.
            merchant: Merchant name.
            raw_text: Raw text extracted from PDF.

        Returns:
            The created Transaction object.
        """
        async with self.async_session() as session:
            transaction = Transaction(
                transaction_id=transaction_id,
                date=date,
                description=description,
                amount=amount,
                transaction_type=transaction_type,
                category=category,
                merchant=merchant,
                raw_text=raw_text,
            )
            session.add(transaction)
            await session.commit()
            await session.refresh(transaction)
            return transaction

    async def get_transaction_by_id(self, transaction_id: str) -> Transaction | None:
        """Get a transaction by its transaction ID asynchronously.

        Args:
            transaction_id: The transaction ID to search for.

        Returns:
            The Transaction if found, None otherwise.
        """
        from sqlalchemy import select

        async with self.async_session() as session:
            result = await session.execute(
                select(Transaction).filter(Transaction.transaction_id == transaction_id)
            )
            return result.scalar_one_or_none()

    async def get_all_transactions(self) -> list[Transaction]:
        """Get all transactions from the database asynchronously.

        Returns:
            List of all transactions.
        """
        from sqlalchemy import select

        async with self.async_session() as session:
            result = await session.execute(select(Transaction))
            return list(result.scalars().all())

    async def transaction_exists(self, transaction_id: str) -> bool:
        """Check if a transaction already exists asynchronously.

        Args:
            transaction_id: The transaction ID to check.

        Returns:
            True if transaction exists, False otherwise.
        """
        transaction = await self.get_transaction_by_id(transaction_id)
        return transaction is not None

    async def close(self) -> None:
        """Close the database engine and release resources."""
        await self.engine.dispose()
