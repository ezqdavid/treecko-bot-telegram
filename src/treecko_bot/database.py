"""SQLite database models and operations."""

from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Float, Integer, String, create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

Base = declarative_base()


def _utc_now():
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

    def __init__(self, database_path: str):
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
