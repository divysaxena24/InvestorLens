
"""Tests for PDF metadata extraction and page-number handling."""

from unittest.mock import MagicMock

import pymupdf

from app.ingestion.metadata import MetadataExtractor


def test_metadata_extraction_with_offset():
    extractor = MetadataExtractor()

    # Mock page rect: 594 x 756
    page = MagicMock()
    page.rect = pymupdf.Rect(0, 0, 594, 756)

    # Header block containing section title and printed page number.
    header_block = (
        51.4,
        19.5,
        218.9,
        32.0,
        "Stan d alo n e Fin an c ial Statemen ts 2024-25\n305\n",
        0,
        0,
    )

    # Footer block.
    footer_block = (
        248.9,
        728.0,
        345.0,
        736.6,
        "Integrated Annual Report 2024-25\n",
        1,
        0,
    )

    page.get_text.return_value = [header_block, footer_block]

    # PDF page 307 corresponds to printed page 305.
    printed_page, section = extractor.extract_page_metadata(
        page, pdf_page=307
    )

    assert printed_page == 305
    assert section == "Standalone Financial Statements"


def test_metadata_extraction_unknown_when_no_header():
    extractor = MetadataExtractor()
    page = MagicMock()
    page.rect = pymupdf.Rect(0, 0, 594, 756)

    # No header or footer blocks.
    page.get_text.return_value = []

    printed_page, section = extractor.extract_page_metadata(
        page, pdf_page=1
    )

    assert printed_page is None
    assert section is None


def test_metadata_extraction_unnumbered_page():
    extractor = MetadataExtractor()
    page = MagicMock()
    page.rect = pymupdf.Rect(0, 0, 594, 756)

    # Header with title but no page number.
    header_block = (
        50.0,
        20.0,
        300.0,
        35.0,
        "Management Discussion and Analysis\n",
        0,
        0,
    )

    page.get_text.return_value = [header_block]

    printed_page, section = extractor.extract_page_metadata(
        page, pdf_page=15
    )

    assert printed_page is None
    assert section == "Management Discussion and Analysis"


def test_metadata_extraction_roman_numeral_or_non_integer():
    extractor = MetadataExtractor()
    page = MagicMock()
    page.rect = pymupdf.Rect(0, 0, 594, 756)

    # Header with Roman numeral front matter like "Page iv".
    header_block = (
        50.0,
        20.0,
        300.0,
        35.0,
        "Notice of Annual General Meeting\nPage iv\n",
        0,
        0,
    )

    page.get_text.return_value = [header_block]

    # Non-integer page numbers should not be converted to integers.
    printed_page, _section = extractor.extract_page_metadata(
        page, pdf_page=307
    )
    assert printed_page is None


def test_metadata_extraction_ignores_deep_body_blocks():
    extractor = MetadataExtractor()
    page = MagicMock()
    page.rect = pymupdf.Rect(0, 0, 594, 756)

    # Body block containing numbers that should not be treated as page numbers.
    body_block = (
        100.0,
        62.0,
        500.0,
        700.0,
        "Total Assets 255 crore\n",
        0,
        0,
    )

    page.get_text.return_value = [body_block]

    printed_page, section = extractor.extract_page_metadata(
        page, pdf_page=254
    )

    assert printed_page is None
    assert section is None
