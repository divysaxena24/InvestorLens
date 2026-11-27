
from uuid import uuid4

import numpy as np
import pytest

from app.ingestion.chunker import DocumentChunk
from app.vectorstore.ingestion import (
    generate_point_id,
    upsert_document_chunks,
)


class FakeQdrantClient:
    def __init__(self):
        self.points = {}

    def upsert(self, collection_name, points, wait):
        assert collection_name == "investorlens_chunks"
        assert wait is True

        for point in points:
            self.points[str(point.id)] = point


@pytest.fixture
def document_id():
    return str(uuid4())


@pytest.fixture
def user_id():
    return str(uuid4())


@pytest.fixture
def sample_chunk(document_id):
    return DocumentChunk(
        chunk_id=f"{document_id}_p1_001",
        document_id=document_id,
        content="Revenue increased by 12% during FY2025.",
        page_start=1,
        page_end=1,
        printed_page=1,
        section="Financial Performance",
        content_type="text",
        extraction_method="native",
        review_required=False,
        quality_flags=[],
    )


def test_generate_point_id_is_deterministic(document_id):
    first = generate_point_id(document_id, "chunk-1")
    second = generate_point_id(document_id, "chunk-1")
    different = generate_point_id(document_id, "chunk-2")

    assert first == second
    assert first != different


def test_upsert_document_chunks_success(
    document_id,
    user_id,
    sample_chunk,
):
    client = FakeQdrantClient()
    vector = np.zeros(384, dtype=np.float32)
    vector[0] = 1.0

    count = upsert_document_chunks(
        client=client,
        chunks=[sample_chunk],
        vectors=[vector.tolist()],
        user_id=user_id,
        document_id=document_id,
    )

    assert count == 1
    assert len(client.points) == 1

    point = next(iter(client.points.values()))

    assert point.payload["chunk_id"] == sample_chunk.chunk_id
    assert point.payload["document_id"] == document_id
    assert point.payload["user_id"] == user_id
    assert point.payload["content"] == sample_chunk.content
    assert point.payload["section"] == "Financial Performance"
    assert len(point.vector) == 384


def test_upsert_is_idempotent(
    document_id,
    user_id,
    sample_chunk,
):
    client = FakeQdrantClient()
    vector = np.zeros(384, dtype=np.float32)
    vector[0] = 1.0

    for _ in range(2):
        upsert_document_chunks(
            client=client,
            chunks=[sample_chunk],
            vectors=[vector.tolist()],
            user_id=user_id,
            document_id=document_id,
        )

    assert len(client.points) == 1


def test_rejects_mismatched_chunk_and_vector_counts(
    document_id,
    user_id,
    sample_chunk,
):
    with pytest.raises(ValueError, match="count"):
        upsert_document_chunks(
            client=FakeQdrantClient(),
            chunks=[sample_chunk],
            vectors=[],
            user_id=user_id,
            document_id=document_id,
        )


def test_rejects_wrong_vector_dimensions(
    document_id,
    user_id,
    sample_chunk,
):
    with pytest.raises(ValueError, match="384"):
        upsert_document_chunks(
            client=FakeQdrantClient(),
            chunks=[sample_chunk],
            vectors=[[0.1, 0.2, 0.3]],
            user_id=user_id,
            document_id=document_id,
        )


def test_rejects_non_finite_vectors(
    document_id,
    user_id,
    sample_chunk,
):
    vector = np.zeros(384, dtype=np.float32)
    vector[0] = np.nan

    with pytest.raises(ValueError, match="non-finite"):
        upsert_document_chunks(
            client=FakeQdrantClient(),
            chunks=[sample_chunk],
            vectors=[vector.tolist()],
            user_id=user_id,
            document_id=document_id,
        )


def test_rejects_chunk_from_another_document(
    document_id,
    user_id,
    sample_chunk,
):
    another_document_id = str(uuid4())
    sample_chunk.document_id = another_document_id

    with pytest.raises(ValueError, match="another document"):
        upsert_document_chunks(
            client=FakeQdrantClient(),
            chunks=[sample_chunk],
            vectors=[[1.0] + [0.0] * 383],
            user_id=user_id,
            document_id=document_id,
        )


def test_rejects_duplicate_chunk_ids(
    document_id,
    user_id,
    sample_chunk,
):
    duplicate = DocumentChunk(
        **{
            **sample_chunk.__dict__,
            "content": "Duplicate chunk content",
        }
    )

    with pytest.raises(ValueError, match="Duplicate chunk IDs"):
        upsert_document_chunks(
            client=FakeQdrantClient(),
            chunks=[sample_chunk, duplicate],
            vectors=[
                [1.0] + [0.0] * 383,
                [0.0, 1.0] + [0.0] * 382,
            ],
            user_id=user_id,
            document_id=document_id,
        )


def test_upsert_respects_batch_size(
    document_id,
    user_id,
    sample_chunk,
):
    class BatchTrackingClient(FakeQdrantClient):
        def __init__(self):
            super().__init__()
            self.batch_sizes = []

        def upsert(self, collection_name, points, wait):
            self.batch_sizes.append(len(points))
            super().upsert(collection_name, points, wait)

    client = BatchTrackingClient()
    chunks = [
        DocumentChunk(
            **{
                **sample_chunk.__dict__,
                "chunk_id": f"{document_id}_chunk_{i}",
            }
        )
        for i in range(3)
    ]
    vectors = [
        [1.0] + [0.0] * 383,
        [0.0, 1.0] + [0.0] * 382,
        [0.0, 0.0, 1.0] + [0.0] * 381,
    ]

    upsert_document_chunks(
        client=client,
        chunks=chunks,
        vectors=vectors,
        user_id=user_id,
        document_id=document_id,
        batch_size=2,
    )

    assert client.batch_sizes == [2, 1]