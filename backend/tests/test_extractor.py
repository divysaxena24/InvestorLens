"""Tests for the PDF extraction pipeline end-to-end functionality."""

import csv
from pathlib import Path

import pymupdf
import pytest

from app.ingestion.extractor import PDFExtractionPipeline


@pytest.fixture
def sample_pdf(tmp_path: Path) -> Path:
    """Creates a temporary 2-page PDF for test isolation."""
    pdf_path = tmp_path / "sample.pdf"
    doc = pymupdf.open()

    # Page 1: Short intro
    page1 = doc.new_page(width=594, height=756)
    page1.insert_text(
        (50, 40), "Standalone Financial Statements 2024-25\n10", fontsize=10
    )
    page1.insert_text(
        (50, 100), "This is a clean page with reliable extraction content.", fontsize=12
    )

    # Page 2: Empty page
    doc.new_page(width=594, height=756)

    doc.save(str(pdf_path))
    doc.close()
    return pdf_path


def test_native_extraction_pipeline(sample_pdf: Path, tmp_path: Path):
    pipeline = PDFExtractionPipeline()

    pages = pipeline.extract_native(sample_pdf)
    assert len(pages) == 2

    # Check page 1
    p1 = pages[0]
    assert p1.pdf_page == 1
    assert p1.printed_page == 10
    assert p1.section == "Standalone Financial Statements"
    assert "clean page" in p1.text
    assert p1.extraction_method == "native"

    # Check page 2 (empty page)
    p2 = pages[1]
    assert p2.pdf_page == 2
    assert "EMPTY_PAGE" in p2.quality_flags
    assert p2.review_required is True

    # Check markdown save
    md_path = tmp_path / "output.md"
    pipeline.save_markdown(pages, md_path)
    assert md_path.exists()
    content = md_path.read_text(encoding="utf-8")
    assert "<!-- Page 1 | Printed: 10 | Section: Standalone Financial Statements | Method: native -->" in content

    # Check quality CSV report
    csv_path = tmp_path / "quality_report.csv"
    pipeline.save_quality_report(pages, csv_path)
    assert csv_path.exists()

    with open(csv_path, encoding="utf-8") as f:
        reader = list(csv.DictReader(f))
        assert len(reader) == 2
        assert reader[0]["pdf_page"] == "1"
        assert reader[0]["printed_page"] == "10"
        assert reader[0]["review_required"] == "False"
        assert reader[1]["pdf_page"] == "2"
        assert reader[1]["review_required"] == "True"
        assert "EMPTY_PAGE" in reader[1]["quality_flags"]


def test_selective_ocr_does_not_overwrite_native(sample_pdf: Path, tmp_path: Path):
    pipeline = PDFExtractionPipeline()

    native_pages = pipeline.extract_native(sample_pdf, pages=[1])
    assert len(native_pages) == 1
    native_text = native_pages[0].text

    # Run selective OCR on page 1 only
    ocr_pages = pipeline.extract_ocr_selective(sample_pdf, selected_pages=[1])
    assert len(ocr_pages) == 1
    assert ocr_pages[0].extraction_method == "ocr"

    # Save both separately
    native_file = tmp_path / "native.md"
    ocr_file = tmp_path / "ocr.md"
    pipeline.save_markdown(native_pages, native_file)
    pipeline.save_markdown(ocr_pages, ocr_file)

    assert native_file.exists()
    assert ocr_file.exists()
    assert native_pages[0].text == native_text  # Native remains preserved

