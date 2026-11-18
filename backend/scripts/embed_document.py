"""End-to-end document embedding script for InvestorLens.

Runs the complete ingestion pipeline:
1. Loads raw PDF.
2. Extracts pages with page metadata and quality checks using PDFExtractionPipeline.
3. Chunks pages structure-aware using SemanticChunker.
4. Generates dense embeddings using EmbeddingGenerator (all-MiniLM-L6-v2).
5. Validates vector dimensions, counts, finite values, unit L2 norms, unique chunk IDs, and metadata.
6. Saves vectors in NumPy .npz and chunk metadata in JSON under data/processed/embeddings/.
7. Prints a concise report.

Usage:
    python backend/scripts/embed_document.py [--pdf PATH] [--output-dir DIR] [--device cpu]
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import time
from typing import Sequence

# Ensure backend root is on sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

import numpy as np

from app.ingestion.chunker import DocumentChunk, SemanticChunker
from app.ingestion.embeddings import EmbeddingGenerator
from app.ingestion.extractor import PDFExtractionPipeline
from app.ingestion.models import PageExtraction


def validate_embeddings(
    chunks: Sequence[DocumentChunk],
    vectors: np.ndarray,
    expected_dim: int = 384,
) -> dict[str, bool]:
    """Validates vector array against chunks according to pipeline constraints."""
    validations: dict[str, bool] = {}

    # 1. Number of generated vectors equals number of chunks
    validations["count_matches"] = len(vectors) == len(chunks)

    # 2. Every vector has exactly expected_dim dimensions
    validations["dimensions_correct"] = (
        vectors.ndim == 2 and vectors.shape[1] == expected_dim
    )

    # 3. All vector values are finite
    validations["all_finite"] = bool(np.all(np.isfinite(vectors)))

    # 4. Every vector has approximately unit L2 norm
    norms = np.linalg.norm(vectors, axis=1)
    validations["unit_l2_norms"] = bool(np.allclose(norms, 1.0, atol=1e-4))

    # 5. Chunk IDs are unique
    chunk_ids = [c.chunk_id for c in chunks]
    validations["unique_chunk_ids"] = len(chunk_ids) == len(set(chunk_ids))

    # 6. Chunk metadata is preserved
    all_meta_valid = all(
        c.page_start >= 1
        and c.page_end >= c.page_start
        and c.document_id
        and c.chunk_id
        and c.content_type in {"text", "table"}
        for c in chunks
    )
    validations["metadata_preserved"] = all_meta_valid

    return validations


def save_embeddings_and_metadata(
    chunks: Sequence[DocumentChunk],
    vectors: np.ndarray,
    output_dir: Path,
    stem: str,
) -> tuple[Path, Path]:
    """Saves vectors as compressed NumPy .npz and metadata as JSON."""
    output_dir.mkdir(parents=True, exist_ok=True)

    npz_path = output_dir / f"{stem}_vectors.npz"
    metadata_path = output_dir / f"{stem}_chunks.json"

    # Save vectors to compact compressed npz
    np.savez_compressed(npz_path, vectors=vectors)

    # Prepare JSON serializable metadata
    metadata_list = [
        {
            "chunk_id": c.chunk_id,
            "document_id": c.document_id,
            "content": c.content,
            "page_start": c.page_start,
            "page_end": c.page_end,
            "printed_page": c.printed_page,
            "section": c.section,
            "content_type": c.content_type,
            "extraction_method": c.extraction_method,
            "review_required": c.review_required,
            "quality_flags": c.quality_flags,
            "character_count": len(c.content),
        }
        for c in chunks
    ]

    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata_list, f, indent=2, ensure_ascii=False)

    return npz_path, metadata_path


def run_pipeline(
    pdf_path: Path,
    output_dir: Path,
    document_id: str | None = None,
    device: str = "cpu",
    max_chars: int = 3200,
    overlap_chars: int = 400,
) -> dict:
    """Executes the complete ingestion pipeline for a document."""
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    start_time = time.perf_counter()
    doc_id = document_id or pdf_path.stem

    print("=" * 70)
    print("INVESTORLENS END-TO-END INGESTION & EMBEDDING PIPELINE")
    print("=" * 70)
    print(f"Document: {pdf_path.name}")
    print(f"Output directory: {output_dir}")
    print(f"Device: {device}")
    print(f"Chunk max_chars: {max_chars}, overlap_chars: {overlap_chars}")

    # Stage 1: Extraction
    print("\n[1/4] Extracting PDF pages using PDFExtractionPipeline...")
    t_extract_start = time.perf_counter()
    pipeline = PDFExtractionPipeline()

    def progress(current: int, total: int):
        if current % 50 == 0 or current == total:
            print(f"  Extracted {current}/{total} pages...")

    pages = pipeline.extract_native(pdf_path, progress_callback=progress)
    t_extract = time.perf_counter() - t_extract_start
    print(f"  Extracted {len(pages)} pages in {t_extract:.2f}s")

    # Stage 2: Semantic Chunking
    print("\n[2/4] Chunking pages using SemanticChunker...")
    t_chunk_start = time.perf_counter()
    chunker = SemanticChunker(max_chars=max_chars, overlap_chars=overlap_chars)
    chunks = chunker.chunk_pages(pages, document_id=doc_id)
    t_chunk = time.perf_counter() - t_chunk_start
    print(f"  Generated {len(chunks)} chunks in {t_chunk:.2f}s")

    # Stage 3: Embedding Generation
    print("\n[3/4] Generating embeddings using EmbeddingGenerator...")
    t_embed_start = time.perf_counter()
    generator = EmbeddingGenerator(device=device)
    texts = [c.content for c in chunks]
    vectors_list = generator.generate(texts)
    vectors = np.array(vectors_list, dtype=np.float32)
    t_embed = time.perf_counter() - t_embed_start
    print(f"  Generated {len(vectors)} vectors in {t_embed:.2f}s")

    # Stage 4: Validation
    print("\n[4/4] Validating embeddings and metadata...")
    validations = validate_embeddings(chunks, vectors, expected_dim=generator.EMBEDDING_DIMENSION)
    all_valid = all(validations.values())

    for check, passed in validations.items():
        status = "PASSED" if passed else "FAILED"
        print(f"  - {check}: {status}")

    if not all_valid:
        failed_checks = [k for k, v in validations.items() if not v]
        raise ValueError(f"Embedding validation failed on checks: {failed_checks}")

    # Stage 5: Persistence
    print("\nSaving vectors and metadata...")
    npz_path, json_path = save_embeddings_and_metadata(
        chunks=chunks,
        vectors=vectors,
        output_dir=output_dir,
        stem=doc_id,
    )
    print(f"  Vectors (.npz):   {npz_path} ({npz_path.stat().st_size / 1024:.1f} KB)")
    print(f"  Metadata (.json): {json_path} ({json_path.stat().st_size / 1024:.1f} KB)")

    total_time = time.perf_counter() - start_time

    # Print Summary Report
    print("\n" + "=" * 70)
    print("PIPELINE EXECUTION SUMMARY")
    print("=" * 70)
    print(f"Page Count:         {len(pages)}")
    print(f"Chunk Count:        {len(chunks)}")
    print(f"Embedding Count:    {len(vectors)}")
    print(f"Vector Dimensions:  {vectors.shape[1]}")
    print(f"Extraction Time:    {t_extract:.2f}s")
    print(f"Chunking Time:      {t_chunk:.2f}s")
    print(f"Embedding Time:     {t_embed:.2f}s")
    print(f"Total Processing:   {total_time:.2f}s")
    print(f"Validation Status:  {'ALL CHECKS PASSED' if all_valid else 'VALIDATION FAILED'}")
    print("=" * 70)

    return {
        "pages": len(pages),
        "chunks": len(chunks),
        "embeddings": len(vectors),
        "dimensions": vectors.shape[1],
        "validations": validations,
        "total_time": total_time,
        "npz_path": npz_path,
        "json_path": json_path,
    }


def main():
    parser = argparse.ArgumentParser(description="End-to-End Document Ingestion & Embedding")
    parser.add_argument(
        "--pdf",
        type=Path,
        default=BASE_DIR / "data" / "raw" / "tcs_annual_report_2025.pdf",
        help="Path to input PDF",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=BASE_DIR / "data" / "processed" / "embeddings",
        help="Directory to save embeddings and metadata",
    )
    parser.add_argument(
        "--document-id",
        type=str,
        default=None,
        help="Document ID for chunk naming (default: PDF stem)",
    )
    parser.add_argument(
        "--device",
        type=str,
        default="cpu",
        help="Compute device for SentenceTransformer (cpu or cuda)",
    )
    parser.add_argument(
        "--max-chars",
        type=int,
        default=3200,
        help="Maximum chunk character size",
    )
    parser.add_argument(
        "--overlap-chars",
        type=int,
        default=400,
        help="Overlap character size for text chunks",
    )
    args = parser.parse_args()

    run_pipeline(
        pdf_path=args.pdf,
        output_dir=args.output_dir,
        document_id=args.document_id,
        device=args.device,
        max_chars=args.max_chars,
        overlap_chars=args.overlap_chars,
    )


if __name__ == "__main__":
    main()

