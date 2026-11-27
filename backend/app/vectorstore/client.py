
from qdrant_client import QdrantClient

from app.core.config import settings


def get_qdrant_client() -> QdrantClient:
    """Return a Qdrant client using application settings."""
    return QdrantClient(url=settings.QDRANT_URL)
