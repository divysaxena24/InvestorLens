
"""Load precomputed document embeddings into Qdrant."""

import json
import uuid
from pathlib import Path

import numpy as np
from qdrant_client import QdrantClient, models

from app.vectorstore.collections import COLLECTION_NAME, VECTOR_SIZE

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data" / "processed" / "embeddings"

CHUNKS_PATH = DATA_DIR / "tcs_annual_report_2025_chunks.json"
VECTORS_PATH = DATA_DIR / "tcs_annual_report_2025_vectors.npz"

QDRANT_URL = "http://localhost:6333"
BATCH_SIZE = 64

# Stable namespace: the same chunk_id always produces the same UUID.
POINT_NAMESPACE = uuid.UUID("a4b6f8e2-3c91-4d75-9a20-6f1b8c5e7d30")


def load_artifacts():
    with CHUNKS_PATH.open("r", encoding="utf-8") as file:
        chunks = json.load(file)

    with np.load(VECTORS_PATH) as archive:
        vectors = archive["vectors"].copy()

    if not isinstance(chunks, list):
        raise TypeError("Chunks JSON must contain a list")

    if vectors.shape != (len(chunks), VECTOR_SIZE):
        raise ValueError(
            f"Expected vectors shape ({len(chunks)}, {VECTOR_SIZE}), "
            f"got {vectors.shape}"
        )

    if not np.isfinite(vectors).all():
        raise ValueError("Vectors contain NaN or infinite values")

    chunk_ids = [chunk["chunk_id"] for chunk in chunks]

    if len(chunk_ids) != len(set(chunk_ids)):
        raise ValueError("Duplicate chunk IDs found")

    if any(not chunk.get("content", "").strip() for chunk in chunks):
        raise ValueError("One or more chunks have empty content")

    return chunks, vectors


def create_points(chunks, vectors):
    points = []

    for chunk, vector in zip(chunks, vectors):
        point_id = str(
            uuid.uuid5(POINT_NAMESPACE, chunk["chunk_id"])
        )

        payload = {
            "chunk_id": chunk["chunk_id"],
            "document_id": chunk["document_id"],
            "content": chunk["content"],
            "page_start": chunk["page_start"],
            "page_end": chunk["page_end"],
            "printed_page": chunk.get("printed_page"),
            "section": chunk.get("section"),
            "content_type": chunk.get("content_type"),
            "extraction_method": chunk.get("extraction_method"),
            "review_required": chunk.get("review_required", False),
            "quality_flags": chunk.get("quality_flags", []),
        }

        points.append(
            models.PointStruct(
                id=point_id,
                vector=vector.tolist(),
                payload=payload,
            )
        )

    return points


def ingest():
    chunks, vectors = load_artifacts()

    document_ids = {chunk["document_id"] for chunk in chunks}
    if len(document_ids) != 1:
        raise ValueError("Expected chunks from exactly one document")

    client = QdrantClient(url=QDRANT_URL)

    try:
        collection = client.get_collection(COLLECTION_NAME)
        configured_size = collection.config.params.vectors.size

        if configured_size != VECTOR_SIZE:
            raise ValueError(
                f"Collection dimension mismatch: {configured_size}"
            )

        points = create_points(chunks, vectors)

        for start in range(0, len(points), BATCH_SIZE):
            batch = points[start:start + BATCH_SIZE]

            client.upsert(
                collection_name=COLLECTION_NAME,
                points=batch,
                wait=True,
            )

            print(
                f"Uploaded {min(start + len(batch), len(points))}"
                f"/{len(points)} points"
            )

        result = client.count(
            collection_name=COLLECTION_NAME,
            exact=True,
        )

        print("\nIngestion completed")
        print("Document:", next(iter(document_ids)))
        print("Chunks processed:", len(chunks))
        print("Points in collection:", result.count)

    finally:
        client.close()


if __name__ == "__main__":
    ingest()
