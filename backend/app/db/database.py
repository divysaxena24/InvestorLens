
import os
from pathlib import Path
from typing import Generator

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

# Load backend/.env
BACKEND_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BACKEND_DIR / ".env")

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is missing from backend/.env")

# Configure Psycopg 3 driver
url = make_url(DATABASE_URL)

if url.drivername in ("postgresql", "postgres"):
    url = url.set(drivername="postgresql+psycopg")

# SQLAlchemy engine
engine = create_engine(
    url,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=5,
)

# Base class for all database models
class Base(DeclarativeBase):
    pass


# Database session factory
SessionLocal = sessionmaker(
    bind=engine,
    class_=Session,
    autoflush=False,
    expire_on_commit=False,
)


# FastAPI database dependency
def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Connection verification
def test_connection():
    """Verify connectivity to PostgreSQL."""
    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1"))
        return result.scalar_one()
