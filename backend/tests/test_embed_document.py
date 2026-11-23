"""Unit and integration tests for embed_document pipeline script."""

import json
from pathlib import Path

import numpy as np
import pytest

from app.ingestion.chunker import DocumentChunk
from scripts.embed_document import (
    save_embeddings_and_metadata,
    validate_embeddings,
)


@pytest.fixture
def sample_chunks():
    return [
        DocumentChunk(
            chunk_id=f"doc_p{i}_001",
            document_id="doc_test",
            content=f"Sample text content for chunk {i}",
            page_start=i,
            page_end=i,
            printed_page=i,
            section="Financial Statements",
            content_type="text",
            extraction_method="native",
            review_required=(i % 2 == 0),
            quality_flags=["UNICODE_REPLACEMENT_CHAR(1)"] if (i % 2 == 0) else [],
        )
        for i in range(1, 4)
    ]


@pytest.fixture
def sample_vectors():
    # 3 unit vectors in 384 dimensions
    vecs = np.zeros((3, 384), dtype=np.float32)
    vecs[0, 0] = 1.0
    vecs[1, 1] = 1.0
    vecs[2, 2] = 1.0
    return vecs


def test_validate_embeddings_passes(sample_chunks, sample_vectors):
    validations = validate_embeddings(sample_chunks, sample_vectors, expected_dim=384)
    assert all(validations.values())
    assert validations["count_matches"] is True
    assert validations["dimensions_correct"] is True
    assert validations["all_finite"] is True
    assert validations["unit_l2_norms"] is True
    assert validations["unique_chunk_ids"] is True
    assert validations["metadata_preserved"] is True


def test_validate_embeddings_detects_count_mismatch(sample_chunks, sample_vectors):
    # Only 2 vectors for 3 chunks
    bad_vectors = sample_vectors[:2]
    validations = validate_embeddings(sample_chunks, bad_vectors, expected_dim=384)
    assert validations["count_matches"] is False


def test_validate_embeddings_detects_wrong_dimensions(sample_chunks):
    bad_dim_vectors = np.ones((3, 128), dtype=np.float32)
    validations = validate_embeddings(sample_chunks, bad_dim_vectors, expected_dim=384)
    assert validations["dimensions_correct"] is False


def test_validate_embeddings_detects_nan_inf(sample_chunks, sample_vectors):
    bad_vectors = sample_vectors.copy()
    bad_vectors[0, 0] = np.nan
    validations = validate_embeddings(sample_chunks, bad_vectors, expected_dim=384)
    assert validations["all_finite"] is False


def test_validate_embeddings_detects_non_unit_norm(sample_chunks, sample_vectors):
    bad_vectors = sample_vectors.copy()
    bad_vectors[0, 0] = 2.0  # Norm is 2.0 instead of 1.0
    validations = validate_embeddings(sample_chunks, bad_vectors, expected_dim=384)
    assert validations["unit_l2_norms"] is False


def test_validate_embeddings_detects_duplicate_chunk_ids(sample_vectors):
    duplicate_chunks = [
        DocumentChunk(
            chunk_id="duplicate_id",
            document_id="doc",
            content="content 1",
            page_start=1,
            page_end=1,
            printed_page=1,
            section=None,
            content_type="text",
            extraction_method="native",
            review_required=False,
        ),
        DocumentChunk(
            chunk_id="duplicate_id",
            document_id="doc",
            content="content 2",
            page_start=2,
            page_end=2,
            printed_page=2,
            section=None,
            content_type="text",
            extraction_method="native",
            review_required=False,
        ),
        DocumentChunk(
            chunk_id="unique_id",
            document_id="doc",
            content="content 3",
            page_start=3,
            page_end=3,
            printed_page=3,
            section=None,
            content_type="text",
            extraction_method="native",
            review_required=False,
        ),
    ]
    validations = validate_embeddings(duplicate_chunks, sample_vectors, expected_dim=384)
    assert validations["unique_chunk_ids"] is False


def test_save_embeddings_and_metadata(tmp_path: Path, sample_chunks, sample_vectors):
    npz_path, json_path = save_embeddings_and_metadata(
        chunks=sample_chunks,
        vectors=sample_vectors,
        output_dir=tmp_path,
        stem="test_doc",
    )

    assert npz_path.exists()
    assert json_path.exists()

    # Verify npz
    with np.load(npz_path) as loaded:
        assert "vectors" in loaded
        assert loaded["vectors"].shape == (3, 384)
        np.testing.assert_allclose(loaded["vectors"], sample_vectors)

    # Verify json
    with open(json_path, encoding="utf-8") as f:
        meta = json.load(f)
    assert len(meta) == 3
    assert meta[0]["chunk_id"] == "doc_p1_001"
    assert meta[0]["page_start"] == 1
    assert meta[0]["review_required"] is False
    assert meta[1]["review_required"] is True
    assert meta[1]["quality_flags"] == ["UNICODE_REPLACEMENT_CHAR(1)"]

