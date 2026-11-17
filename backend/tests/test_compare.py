"""Tests for comparison logic between native and OCR extractions."""

from app.ingestion.compare import compare_extractions
from app.ingestion.models import PageExtraction


def test_comparison_detects_discrepancies():
    native = PageExtraction(
        pdf_page=307,
        printed_page=305,
        section="Standalone Financial Statements",
        text="Current ratio 2.1 2.2. Debt-Equity ratio 0.1 0.1.",
        extraction_method="native",
    )
    ocr = PageExtraction(
        pdf_page=307,
        printed_page=305,
        section="Standalone Financial Statements",
        text="Current ratio 2.1 2.5. Debt-Equity ratio 0.1 0.1.",  # Disagreement in 2.2 vs 2.5
        extraction_method="ocr",
    )

    comp = compare_extractions(native, ocr)
    assert comp.review_required is True
    assert any("Numerical differences detected" in note for note in comp.notes)
    # Native should remain untouched
    assert native.text == "Current ratio 2.1 2.2. Debt-Equity ratio 0.1 0.1."


def test_comparison_identical_text():
    native = PageExtraction(
        pdf_page=10,
        text="Executive summary of operations and milestones.",
        extraction_method="native",
    )
    ocr = PageExtraction(
        pdf_page=10,
        text="Executive summary of operations and milestones.",
        extraction_method="ocr",
    )

    comp = compare_extractions(native, ocr)
    assert comp.similarity_ratio == 1.0
    assert comp.review_required is False

