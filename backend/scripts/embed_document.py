"""End-to-end document embedding script for InvestorLens.

Runs the complete ingestion pipeline:
1. Loads the input PDF.
2. Extracts pages with metadata and quality checks.
3. Generates structure-aware chunks.
4. Generates dense embeddings.
5. Validates vectors and chunk metadata.
6. Saves vectors and metadata.
7. Prints a processing report.

Usage:
    python scripts/embed_document.py [--pdf PATH] [--output-dir DIR]
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

# Ensure backend root is on sys.path.
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

import numpy as np

from app.ingestion.artifacts import (
    save_embeddings_and_metadata,
    validate_embeddings,
)
from app.ingestion.chunker import SemanticChunker
from app.ingestion.embeddings import EmbeddingGenerator
from app.ingestion.extractor import PDFExtractionPipeline


def run_pipeline(
    pdf_path: Path,
    output_dir: Path,
    document_id: str | None = None,
    device: str = "cpu",
    max_chars: int = 3200,
    overlap_chars: int = 400,
) -> dict:
    """Execute the complete ingestion and embedding pipeline."""

    if not pdf_path.is_file():
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

    # Stage 1: Extraction.
    print("\n[1/5] Extracting PDF pages...")
    t_extract_start = time.perf_counter()

    pipeline = PDFExtractionPipeline()

    def progress(current: int, total: int) -> None:
        if current % 50 == 0 or current == total:
            print(f"  Extracted {current}/{total} pages...")

    pages = pipeline.extract_native(
        pdf_path,
        progress_callback=progress,
    )

    t_extract = time.perf_counter() - t_extract_start
    print(f"  Extracted {len(pages)} pages in {t_extract:.2f}s")

    if not pages:
        raise ValueError("No pages could be extracted from the PDF")

    # Stage 2: Chunking.
    print("\n[2/5] Generating structure-aware chunks...")
    t_chunk_start = time.perf_counter()

    chunker = SemanticChunker(
        max_chars=max_chars,
        overlap_chars=overlap_chars,
    )

    chunks = chunker.chunk_pages(
        pages,
        document_id=doc_id,
    )

    t_chunk = time.perf_counter() - t_chunk_start
    print(f"  Generated {len(chunks)} chunks in {t_chunk:.2f}s")

    if not chunks:
        raise ValueError("No chunks could be generated from the PDF")

    # Stage 3: Embedding generation.
    print("\n[3/5] Generating dense embeddings...")
    t_embed_start = time.perf_counter()

    generator = EmbeddingGenerator(device=device)

    texts = [chunk.content for chunk in chunks]

    vectors = np.asarray(
        generator.generate(texts),
        dtype=np.float32,
    )

    t_embed = time.perf_counter() - t_embed_start
    print(f"  Generated {len(vectors)} vectors in {t_embed:.2f}s")

    # Stage 4: Validation.
    print("\n[4/5] Validating embeddings and metadata...")

    validations = validate_embeddings(
        chunks,
        vectors,
        expected_dim=generator.EMBEDDING_DIMENSION,
    )

    all_valid = all(validations.values())

    for check, passed in validations.items():
        status = "PASSED" if passed else "FAILED"
        print(f"  - {check}: {status}")

    if not all_valid:
        failed_checks = [check for check, passed in validations.items() if not passed]
        raise ValueError(f"Embedding validation failed: {failed_checks}")

    # Stage 5: Persistence.
    print("\n[5/5] Saving vectors and chunk metadata...")

    npz_path, json_path = save_embeddings_and_metadata(
        chunks=chunks,
        vectors=vectors,
        output_dir=output_dir,
        stem=doc_id,
    )

    print(f"  Vectors (.npz):   {npz_path} ({npz_path.stat().st_size / 1024:.1f} KB)")
    print(f"  Metadata (.json): {json_path} ({json_path.stat().st_size / 1024:.1f} KB)")

    total_time = time.perf_counter() - start_time

    # Summary report.
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
    print("Validation Status:  ALL CHECKS PASSED")
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


def main() -> None:
    """Parse command-line arguments and run the pipeline."""

    parser = argparse.ArgumentParser(
        description="End-to-End Document Ingestion & Embedding"
    )

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
