from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

# SQLite database URL — use /home/user/ so it's writable under HF Spaces uid 1000
_DB_DIR = os.environ.get("DB_DIR", "/home/user")
os.makedirs(_DB_DIR, exist_ok=True)
DATABASE_URL = f"sqlite:///{_DB_DIR}/underwriting.db"

# Create SQLAlchemy engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # Required for SQLite
    echo=False  # Set to True for SQL logging
)

# Create session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


def get_db():
    """
    Dependency for FastAPI to get database session.
    
    Yields:
        SessionLocal: Database session instance
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
