
"""Qdrant ingestion for InvestorLens document chunks."""

from collections.abc import Sequence
from uuid import NAMESPACE_URL, UUID, uuid5

import numpy as np
from qdrant_client import QdrantClient, models

from app.core.config import settings
from app.ingestion.chunker import DocumentChunk

VECTOR_SIZE = 384
DEFAULT_BATCH_SIZE = 64


def generate_point_id(document_id: str, chunk_id: str) -> str:
    """Generate a stable UUID for a document chunk."""

    return str(
        uuid5(
            NAMESPACE_URL,
            f"investorlens:{UUID(document_id)}:{chunk_id}",
        )
    )


def upsert_document_chunks(
    client: QdrantClient,
    chunks: Sequence[DocumentChunk],
    vectors: Sequence[Sequence[float]],
    user_id: str,
    document_id: str,
    batch_size: int = DEFAULT_BATCH_SIZE,
) -> int:
    """Validate and upsert document chunks with ownership metadata."""

    if not chunks:
        if len(vectors) != 0:
            raise ValueError("Vectors provided without corresponding chunks")
        return 0

    if batch_size <= 0:
        raise ValueError("batch_size must be positive")

    safe_document_id = str(UUID(document_id))
    safe_user_id = str(UUID(user_id))

    vector_array = np.asarray(vectors, dtype=np.float32)

    if len(chunks) != len(vector_array):
	    raise ValueError("Chunk count and vector count do not match")

    if vector_array.ndim != 2:
	    raise ValueError("Vectors must be a two-dimensional array")

    if vector_array.shape[1] != VECTOR_SIZE:
        raise ValueError(
            f"Expected {VECTOR_SIZE}-dimensional vectors, "
            f"got {vector_array.shape[1]}"
        )

    if not np.all(np.isfinite(vector_array)):
        raise ValueError("Vectors contain non-finite values")

    chunk_ids = [chunk.chunk_id for chunk in chunks]

    if len(chunk_ids) != len(set(chunk_ids)):
        raise ValueError("Duplicate chunk IDs are not allowed")

    points = []

    for chunk, vector in zip(chunks, vector_array):
        if chunk.document_id != safe_document_id:
            raise ValueError(
                f"Chunk {chunk.chunk_id} belongs to another document"
            )

        if not chunk.content.strip():
            raise ValueError(f"Chunk {chunk.chunk_id} has empty content")

        point_id = generate_point_id(safe_document_id, chunk.chunk_id)

        payload = {
            "chunk_id": chunk.chunk_id,
            "document_id": safe_document_id,
            "user_id": safe_user_id,
            "content": chunk.content,
            "page_start": chunk.page_start,
            "page_end": chunk.page_end,
            "printed_page": chunk.printed_page,
            "section": chunk.section,
            "content_type": chunk.content_type,
            "extraction_method": chunk.extraction_method,
            "review_required": chunk.review_required,
            "quality_flags": chunk.quality_flags,
        }

        points.append(
            models.PointStruct(
                id=point_id,
                vector=vector.tolist(),
                payload=payload,
            )
        )

    for start in range(0, len(points), batch_size):
        batch = points[start : start + batch_size]

        client.upsert(
            collection_name=settings.QDRANT_COLLECTION,
            points=batch,
            wait=True,
        )

    return len(points)
