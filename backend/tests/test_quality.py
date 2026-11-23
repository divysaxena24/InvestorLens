"""Tests for PDF extraction quality checker."""

import pytest

from app.ingestion.quality import ExtractionQualityChecker


@pytest.fixture
def checker():
    return ExtractionQualityChecker()


def test_empty_page_detection(checker):
    result = checker.check_page("")
    assert "EMPTY_PAGE" in result.quality_flags
    assert result.review_required is True

    result_whitespace = checker.check_page("   \n\n  \t ")
    assert "EMPTY_PAGE" in result_whitespace.quality_flags
    assert result_whitespace.review_required is True


def test_short_page_detection(checker):
    short_text = "This is a very short text."
    result = checker.check_page(short_text)
    assert any("SHORT_PAGE" in f for f in result.quality_flags)


def test_unicode_replacement_character_detection(checker):
    corrupted_text = "Note 2\ufffd: Additional Regulatory Information with value 2.\ufffd%"
    result = checker.check_page(corrupted_text)
    assert any("UNICODE_REPLACEMENT_CHAR" in f for f in result.quality_flags)
    assert result.review_required is True


def test_encoding_corruption_detection(checker):
    mojibake = "The companyâ€™s net profit rose by 10% in FY25."
    result = checker.check_page(mojibake)
    assert any("ENCODING_CORRUPTION" in f for f in result.quality_flags)
    assert result.review_required is True


def test_suspicious_greek_characters_detection(checker):
    # 'ϱ' (U+03F1) replacing '5', 'ϰ' (U+03F0) replacing '4', 'ͻ' (U+037B)
    text_with_greek = "2ϱ) Additional Regulatory Information ͻ Ratios 1051ϰ9"
    result = checker.check_page(text_with_greek)
    assert any("SUSPICIOUS_GREEK_CHARS" in f for f in result.quality_flags)
    assert result.review_required is True


def test_suspicious_digit_spacing(checker):
    text = "Total amount is 1 2 3 4 5 thousand INR."
    result = checker.check_page(text)
    assert any("SUSPICIOUS_DIGIT_SPACING" in f for f in result.quality_flags)


def test_broken_word_spacing(checker):
    text = "Stan d alo n e Fin an c ial Statemen ts 2024-25"
    result = checker.check_page(text)
    assert any("BROKEN_WORD_SPACING" in f for f in result.quality_flags)


def test_clean_financial_page_not_flagged_for_false_positive(checker):
    clean_text = """
# Standalone Financial Statements 2024-25

## Note 25: Additional Regulatory Information

| Ratio | Current year | Previous year |
|---|---|---|
| Current ratio | 2.1 | 2.2 |
| Debt-equity ratio | 0.1 | 0.1 |
| Debt service coverage ratio | 23.5 | 24.0 |
| Return on equity | 65.1% | 59.4% |
| Trade receivables turnover | 4.4 | 4.5 |
| Trade payables turnover | 3.1 | 3.1 |
| Net capital turnover | 4.1 | 3.8 |
| Net profit ratio | 22.4% | 21.5% |
| Return on capital employed | 76.0% | 74.3% |
| Return on investment | 8.5% | 8.3% |
"""
    result = checker.check_page(clean_text)
    assert result.review_required is False
    assert len(result.quality_flags) == 0

