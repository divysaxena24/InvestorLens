"""Data models for PDF extraction, quality checking, and comparison."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Optional


@dataclass
class PageExtraction:
    """Represents the extracted content and metadata of a single PDF page."""

    pdf_page: int  # 1-based PDF page index
    printed_page: Optional[int] = None  # Printed report page number if reliably identified
    section: Optional[str] = None  # Document section name if identified
    text: str = ""  # Extracted Markdown text
    extraction_method: str = "native"  # "native" or "ocr"
    review_required: bool = False
    quality_flags: list[str] = field(default_factory=list)

    @property
    def character_count(self) -> int:
        return len(self.text)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class QualityReportRow:
    """Represents a row in the extraction quality CSV report."""

    pdf_page: int
    printed_page: Optional[int]
    section: Optional[str]
    extraction_method: str
    characters: int
    review_required: bool
    quality_flags: str  # Semicolon-separated quality flags

    def to_csv_dict(self) -> dict[str, Any]:
        return {
            "pdf_page": self.pdf_page,
            "printed_page": "" if self.printed_page is None else self.printed_page,
            "section": self.section if self.section else "Unknown",
            "extraction_method": self.extraction_method,
            "characters": self.characters,
            "review_required": self.review_required,
            "quality_flags": self.quality_flags,
        }


@dataclass
class PageComparison:
    """Comparison result between native and OCR extraction of a single page."""

    pdf_page: int
    native_chars: int
    ocr_chars: int
    char_difference: int
    similarity_ratio: float
    review_required: bool
    notes: list[str] = field(default_factory=list)

