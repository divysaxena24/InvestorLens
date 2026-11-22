
import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

# Load backend/.env
BACKEND_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BACKEND_DIR / ".env")

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is missing from backend/.env")

# Use Psycopg 3 as the PostgreSQL driver
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

def test_connection():
    """Verify connectivity to the PostgreSQL database."""
    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1"))
        return result.scalar_one()
