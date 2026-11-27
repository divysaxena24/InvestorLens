
"""Secure retrieval and deletion of document chunks from Qdrant."""

from collections.abc import Sequence
from uuid import UUID

import numpy as np
from qdrant_client import QdrantClient, models

from app.core.config import settings

VECTOR_SIZE = 384
DEFAULT_SEARCH_LIMIT = 5


def _build_ownership_filter(
    user_id: str,
    document_id: str | None = None,
) -> models.Filter:
    """Build a filter that restricts access to owned document chunks."""

    safe_user_id = str(UUID(user_id))

    conditions = [
        models.FieldCondition(
            key="user_id",
            match=models.MatchValue(value=safe_user_id),
        )
    ]

    if document_id is not None:
        safe_document_id = str(UUID(document_id))

        conditions.append(
            models.FieldCondition(
                key="document_id",
                match=models.MatchValue(value=safe_document_id),
            )
        )

    return models.Filter(must=conditions)


def search_document_chunks(
    client: QdrantClient,
    query_vector: Sequence[float],
    user_id: str,
    document_id: str | None = None,
    limit: int = DEFAULT_SEARCH_LIMIT,
) -> list[models.ScoredPoint]:
    """Search document chunks while enforcing user ownership."""

    if limit <= 0:
        raise ValueError("Search limit must be positive")

    vector = np.asarray(query_vector, dtype=np.float32)

    if vector.ndim != 1 or vector.shape[0] != VECTOR_SIZE:
        raise ValueError(
            f"Query vector must contain exactly {VECTOR_SIZE} dimensions"
        )

    if not np.all(np.isfinite(vector)):
        raise ValueError("Query vector contains non-finite values")

    query_filter = _build_ownership_filter(
        user_id=user_id,
        document_id=document_id,
    )

    response = client.query_points(
        collection_name=settings.QDRANT_COLLECTION,
        query=vector.tolist(),
        query_filter=query_filter,
        limit=limit,
        with_payload=True,
        with_vectors=False,
    )

    return response.points


def delete_document_chunks(
    client: QdrantClient,
    user_id: str,
    document_id: str,
) -> None:
    """Delete all chunks belonging to a specific user's document."""

    query_filter = _build_ownership_filter(
        user_id=user_id,
        document_id=document_id,
    )

    client.delete(
        collection_name=settings.QDRANT_COLLECTION,
        points_selector=models.FilterSelector(
            filter=query_filter,
        ),
        wait=True,
    )
