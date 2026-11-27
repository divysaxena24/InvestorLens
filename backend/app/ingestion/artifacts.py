
"""Embedding validation and artifact persistence for InvestorLens."""

import json
from collections.abc import Sequence
from pathlib import Path

import numpy as np

from app.ingestion.chunker import DocumentChunk


def validate_embeddings(
    chunks: Sequence[DocumentChunk],
    vectors: np.ndarray,
    expected_dim: int = 384,
) -> dict[str, bool]:
    """Validate generated vectors and their corresponding chunk metadata."""

    vectors = np.asarray(vectors)

    count_matches = (
        vectors.ndim == 2 and len(vectors) == len(chunks)
    )

    dimensions_correct = (
        vectors.ndim == 2 and vectors.shape[1] == expected_dim
    )

    all_finite = bool(np.all(np.isfinite(vectors)))

    unit_l2_norms = False
    if vectors.ndim == 2 and vectors.shape[0] > 0:
        norms = np.linalg.norm(vectors, axis=1)
        unit_l2_norms = bool(np.allclose(norms, 1.0, atol=1e-4))
    elif vectors.ndim == 2 and vectors.shape[0] == 0:
        unit_l2_norms = len(chunks) == 0

    chunk_ids = [chunk.chunk_id for chunk in chunks]
    unique_chunk_ids = len(chunk_ids) == len(set(chunk_ids))

    metadata_preserved = all(
        chunk.page_start >= 1
        and chunk.page_end >= chunk.page_start
        and bool(chunk.document_id)
        and bool(chunk.chunk_id)
        and chunk.content_type in {"text", "table"}
        for chunk in chunks
    )

    return {
        "count_matches": count_matches,
        "dimensions_correct": dimensions_correct,
        "all_finite": all_finite,
        "unit_l2_norms": unit_l2_norms,
        "unique_chunk_ids": unique_chunk_ids,
        "metadata_preserved": metadata_preserved,
    }


def save_embeddings_and_metadata(
    chunks: Sequence[DocumentChunk],
    vectors: np.ndarray,
    output_dir: Path,
    stem: str,
) -> tuple[Path, Path]:
    """Save vectors as compressed NPZ and chunk metadata as JSON."""

    output_dir.mkdir(parents=True, exist_ok=True)

    npz_path = output_dir / f"{stem}_vectors.npz"
    metadata_path = output_dir / f"{stem}_chunks.json"

    np.savez_compressed(npz_path, vectors=vectors)

    metadata = [
        {
            "chunk_id": chunk.chunk_id,
            "document_id": chunk.document_id,
            "content": chunk.content,
            "page_start": chunk.page_start,
            "page_end": chunk.page_end,
            "printed_page": chunk.printed_page,
            "section": chunk.section,
            "content_type": chunk.content_type,
            "extraction_method": chunk.extraction_method,
            "review_required": chunk.review_required,
            "quality_flags": chunk.quality_flags,
            "character_count": len(chunk.content),
        }
        for chunk in chunks
    ]

    metadata_path.write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    return npz_path, metadata_path
