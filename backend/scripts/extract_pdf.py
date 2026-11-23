"""PDF extraction and quality reporting script.

Usage:
    python backend/scripts/extract_pdf.py [--pdf PATH] [--output-dir DIR]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Ensure backend root is on sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from app.ingestion.extractor import PDFExtractionPipeline


def run_extraction(pdf_path: Path, output_dir: Path):
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    output_dir.mkdir(parents=True, exist_ok=True)
    pipeline = PDFExtractionPipeline()

    print(f"Starting extraction for: {pdf_path.name}")
    print(f"Target directory: {output_dir}")

    # 1. Native Extraction of all pages
    def progress(current, total):
        if current % 25 == 0 or current == total:
            print(f"  Processed {current}/{total} pages...")

    pages = pipeline.extract_native(pdf_path, progress_callback=progress)

    # 2. Save Native Markdown
    markdown_path = output_dir / f"{pdf_path.stem}.md"
    pipeline.save_markdown(pages, markdown_path)
    print(f"\nNative Markdown saved: {markdown_path}")

    # 3. Save Quality Report CSV
    quality_csv_path = output_dir / f"{pdf_path.stem}_quality_report.csv"
    pipeline.save_quality_report(pages, quality_csv_path)
    print(f"Quality report CSV saved: {quality_csv_path}")

    # Compute summary metrics
    total_pages = len(pages)
    flagged_pages = sum(1 for p in pages if p.quality_flags)
    review_required_pages = sum(1 for p in pages if p.review_required)
    total_chars = sum(p.character_count for p in pages)

    print("\n" + "=" * 60)
    print("EXTRACTION SUMMARY")
    print("=" * 60)
    print(f"Total pages processed: {total_pages}")
    print(f"Total characters: {total_chars:,}")
    print(f"Pages with quality flags: {flagged_pages}")
    print(f"Pages requiring manual review: {review_required_pages}")
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(description="Extract PDF to Markdown with Quality Checks")
    parser.add_argument(
        "--pdf",
        type=Path,
        default=BASE_DIR / "data" / "raw" / "tcs_annual_report_2025.pdf",
        help="Path to PDF file",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=BASE_DIR / "data" / "processed",
        help="Output directory for processed files",
    )
    args = parser.parse_args()
    run_extraction(args.pdf, args.output_dir)


if __name__ == "__main__":
    main()
