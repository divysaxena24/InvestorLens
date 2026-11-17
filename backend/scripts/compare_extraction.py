"""Selective OCR evaluation and comparison against native extraction.

Usage:
    python backend/scripts/compare_extraction.py [--pages 307]
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from app.ingestion.extractor import PDFExtractionPipeline


def compare_pages(pdf_path: Path, pages: list[int], output_dir: Path):
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    pipeline = PDFExtractionPipeline()
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Comparing native vs. OCR extraction for PDF pages: {pages}")

    # Extract Native
    native_pages = pipeline.extract_native(pdf_path, pages=pages)
    # Extract OCR
    ocr_pages = pipeline.extract_ocr_selective(pdf_path, selected_pages=pages)

    ocr_map = {p.pdf_page: p for p in ocr_pages}

    for nat in native_pages:
        ocr = ocr_map.get(nat.pdf_page)
        if not ocr:
            continue

        comp = pipeline.compare_page(nat, ocr)

        print("\n" + "=" * 70)
        print(f"PAGE COMPARISON: PDF Page {nat.pdf_page} (Printed Page {nat.printed_page or 'Unknown'})")
        print("=" * 70)
        print(f"Section: {nat.section or 'Unknown'}")
        print(f"Native characters: {nat.character_count} | Quality flags: {nat.quality_flags}")
        print(f"OCR characters:    {ocr.character_count} | Quality flags: {ocr.quality_flags}")
        print(f"Similarity ratio:  {comp.similarity_ratio:.2%}")
        print(f"Review required:   {comp.review_required}")
        print("Discrepancies / Notes:")
        for note in comp.notes:
            print(f"  - {note}")

        # Save OCR output separately
        ocr_file = output_dir / f"ocr_page_{nat.pdf_page}.md"
        pipeline.save_markdown([ocr], ocr_file)
        print(f"OCR text preserved separately at: {ocr_file}")


def main():
    parser = argparse.ArgumentParser(description="Selective OCR Evaluation and Comparison")
    parser.add_argument(
        "--pdf",
        type=Path,
        default=BASE_DIR / "data" / "raw" / "tcs_annual_report_2025.pdf",
        help="Path to PDF file",
    )
    parser.add_argument(
        "--pages",
        type=int,
        nargs="+",
        default=[307],
        help="PDF page numbers (1-based) to selectively OCR and compare",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=BASE_DIR / "data" / "processed",
        help="Output directory",
    )
    args = parser.parse_args()
    compare_pages(args.pdf, args.pages, args.output_dir)


if __name__ == "__main__":
    main()
