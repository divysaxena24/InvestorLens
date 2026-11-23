
"""Metadata extraction from PDF page headers and footers."""

from __future__ import annotations

import re
from typing import ClassVar

import pymupdf


class MetadataExtractor:
    """Extracts reliable printed page number and document section from a page."""

    KNOWN_SECTIONS: ClassVar[list[str]] = [
        "Standalone Financial Statements",
        "Consolidated Financial Statements",
        "Corporate Governance Report",
        "Management Discussion and Analysis",
        "Business Responsibility and Sustainability Report",
        "Board's Report",
        "Statutory Reports",
        "Financial Statements",
        "Integrated Annual Report",
        "Intellectual Capital",
        "Human Capital",
        "Social and Relationship Capital",
        "Natural Capital",
        "Manufactured Capital",
        "Financial Capital",
    ]

    def __init__(
        self, header_margin: float = 50.0, footer_margin: float = 50.0
    ) -> None:
        self.header_margin = header_margin
        self.footer_margin = footer_margin

    def extract_page_metadata(
        self,
        page: pymupdf.Page,
        pdf_page: int,
    ) -> tuple[int | None, str | None]:
        """Extracts (printed_page, section) without hallucination.

        pdf_page is 1-based.
        """
        rect = page.rect
        page_height = rect.height

        blocks = page.get_text("blocks")

        header_blocks = [
            b
            for b in blocks
            if b[1] <= self.header_margin and b[3] <= 60 and b[4].strip()
        ]
        footer_blocks = [
            b
            for b in blocks
            if b[3] >= (page_height - self.footer_margin)
            and b[1] >= (page_height - 60)
            and b[4].strip()
        ]

        printed_page = self._find_printed_page_number(
            header_blocks, footer_blocks, pdf_page
        )
        section = self._find_section(header_blocks, footer_blocks)

        return printed_page, section

    def _find_printed_page_number(
        self,
        header_blocks: list,
        footer_blocks: list,
        pdf_page: int,
    ) -> int | None:
        """Locates printed page number in headers/footers with sanity validation."""
        candidate_numbers: list[int] = []

        for b in header_blocks + footer_blocks:
            lines = [line.strip() for line in b[4].splitlines() if line.strip()]
            for line in lines:
                if re.fullmatch(r"\d{1,4}", line):
                    candidate_numbers.append(int(line))
                else:
                    match = re.search(r"(?:^|\s)(\d{1,4})(?:\s|$)", line)
                    if match:
                        value = int(match.group(1))
                        if value not in {
                            2024, 2025, 2026, 2023, 2022, 2021, 2020
                        }:
                            candidate_numbers.append(value)

        valid_candidates = [
            num
            for num in candidate_numbers
            if 1 <= num <= 1000 and abs(num - pdf_page) <= 50
        ]

        if valid_candidates:
            valid_candidates.sort(key=lambda num: abs(num - pdf_page))
            return valid_candidates[0]

        return None

    def _find_section(
        self,
        header_blocks: list,
        footer_blocks: list,
    ) -> str | None:
        """Identifies document section from header text without hallucination."""
        combined_header_text = " ".join(b[4] for b in header_blocks)

        for section in self.KNOWN_SECTIONS:
            clean_section = re.sub(r"\s+", "", section).lower()
            clean_header = re.sub(r"\s+", "", combined_header_text).lower()

            if clean_section in clean_header:
                return section

        for block in header_blocks:
            lines = [line.strip() for line in block[4].splitlines() if line.strip()]
            for line in lines:
                if re.fullmatch(r"\d+", line):
                    continue
                if "integrated annual report" in line.lower():
                    continue
                if 5 < len(line) < 80:
                    return line

        return None
