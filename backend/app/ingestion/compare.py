"""Comparison utilities between native extraction and selective OCR results."""

from __future__ import annotations

import difflib
import re
from typing import Optional

from app.ingestion.models import PageComparison, PageExtraction


def compare_extractions(
    native: PageExtraction,
    ocr: PageExtraction,
    similarity_threshold: float = 0.85,
) -> PageComparison:
    """Compares native extraction against OCR extraction for a given page.

    Flags disagreements for manual verification. Never silently replaces
    native financial values with OCR values.
    """
    if native.pdf_page != ocr.pdf_page:
        raise ValueError(
            f"Cannot compare different pages: native={native.pdf_page}, ocr={ocr.pdf_page}"
        )

    native_text = native.text.strip()
    ocr_text = ocr.text.strip()

    native_chars = len(native_text)
    ocr_chars = len(ocr_text)
    char_diff = ocr_chars - native_chars

    # Calculate token-based or character-based similarity ratio
    matcher = difflib.SequenceMatcher(None, native_text, ocr_text)
    similarity = matcher.quick_ratio()

    notes: list[str] = []
    review_required = False

    # Check length divergence
    if native_chars == 0 and ocr_chars > 0:
        notes.append("Native extraction is empty; OCR recovered text.")
        review_required = True
    elif ocr_chars == 0 and native_chars > 0:
        notes.append("OCR extraction is empty; native extraction has text.")
        review_required = True
    elif similarity < similarity_threshold:
        notes.append(
            f"Low extraction similarity ({similarity:.2%}). Substantial text divergence."
        )
        review_required = True

    # Check for number disagreements (extract numbers in tables or text)
    native_numbers = set(re.findall(r"\b\d+(?:\.\d+)?%?\b", native_text))
    ocr_numbers = set(re.findall(r"\b\d+(?:\.\d+)?%?\b", ocr_text))

    disagreed_native = native_numbers - ocr_numbers
    disagreed_ocr = ocr_numbers - native_numbers

    if disagreed_native or disagreed_ocr:
        # Check if there are discrepancies in key numbers
        notable_diffs = list(disagreed_native)[:5]
        notes.append(
            f"Numerical differences detected: {len(disagreed_native)} in native not in OCR, "
            f"{len(disagreed_ocr)} in OCR not in native. Samples: {notable_diffs}"
        )
        # Any numerical disagreement warrants manual review
        review_required = True

    # Check if native had greek character corruptions that OCR may have resolved
    if any("SUSPICIOUS_GREEK" in f or "UNICODE_REPLACEMENT" in f for f in native.quality_flags):
        notes.append("Native extraction had character/font corruptions flagged.")

    return PageComparison(
        pdf_page=native.pdf_page,
        native_chars=native_chars,
        ocr_chars=ocr_chars,
        char_difference=char_diff,
        similarity_ratio=similarity,
        review_required=review_required,
        notes=notes,
    )

