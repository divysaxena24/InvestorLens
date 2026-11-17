"""Metadata extraction from PDF page headers and footers."""

from __future__ import annotations

import re
from typing import Optional
import pymupdf


class MetadataExtractor:
    """Extracts reliable printed page number and document section from a page."""

    # Section normalization patterns
    KNOWN_SECTIONS = [
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

    def __init__(self, header_margin: float = 50.0, footer_margin: float = 50.0) -> None:
        self.header_margin = header_margin
        self.footer_margin = footer_margin

    def extract_page_metadata(
        self,
        page: pymupdf.Page,
        pdf_page: int,
    ) -> tuple[Optional[int], Optional[str]]:
        """Extracts (printed_page, section) without hallucination.

        pdf_page is 1-based.
        """
        rect = page.rect
        page_height = rect.height

        # Blocks: (x0, y0, x1, y1, text, block_no, block_type)
        blocks = page.get_text("blocks")

        # In standard financial reports, running headers occupy the top margin (y1 <= 55)
        # and running footers occupy the bottom margin (y0 >= page_height - 55).
        # We enforce both y0 and y1 bounds so multi-line body tables spanning into
        # the margins are not misidentified as headers/footers.
        header_blocks = [
            b for b in blocks if b[1] <= self.header_margin and b[3] <= 60 and b[4].strip()
        ]
        footer_blocks = [
            b for b in blocks if b[3] >= (page_height - self.footer_margin) and b[1] >= (page_height - 60) and b[4].strip()
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
    ) -> Optional[int]:
        """Locates printed page number in headers/footers with sanity validation."""
        candidate_numbers: list[int] = []

        # Look in header blocks first (most annual reports put page numbers top left/right)
        for b in header_blocks + footer_blocks:
            lines = [line.strip() for line in b[4].splitlines() if line.strip()]
            for line in lines:
                # Check for standalone integer
                if re.fullmatch(r"\d{1,4}", line):
                    candidate_numbers.append(int(line))
                else:
                    # Check if line ends or starts with a standalone page number (e.g. 'Standalone... 305' or '305 Standalone...')
                    m = re.search(r"(?:^|\s)(\d{1,4})(?:\s|$)", line)
                    if m:
                        val = int(m.group(1))
                        # Ignore 4-digit years like 2024, 2025
                        if val not in {2024, 2025, 2026, 2023, 2022, 2021, 2020}:
                            candidate_numbers.append(val)

        # Filter candidates: printed page should generally be close to pdf_page (within reason, e.g. -20 to +10)
        valid_candidates = [
            num for num in candidate_numbers
            if 1 <= num <= 1000 and abs(num - pdf_page) <= 50
        ]

        if valid_candidates:
            # Pick the candidate closest to pdf_page
            valid_candidates.sort(key=lambda n: abs(n - pdf_page))
            return valid_candidates[0]

        return None

    def _find_section(
        self,
        header_blocks: list,
        footer_blocks: list,
    ) -> Optional[str]:
        """Identifies document section from header text without hallucination."""
        # Combine header text
        combined_header_text = " ".join(b[4] for b in header_blocks)

        # First check against known section patterns (allowing slight spacing artifacts)
        for sec in self.KNOWN_SECTIONS:
            # Create regex that allows whitespace between characters if broken spacing occurred
            clean_sec = re.sub(r"\s+", "", sec).lower()
            clean_header = re.sub(r"\s+", "", combined_header_text).lower()
            if clean_sec in clean_header:
                return sec

        # If not in known list, check if there's a clean line in header (excluding standard titles)
        for b in header_blocks:
            lines = [line.strip() for line in b[4].splitlines() if line.strip()]
            for line in lines:
                # Ignore numbers and generic document title
                if re.fullmatch(r"\d+", line):
                    continue
                if "integrated annual report" in line.lower():
                    continue
                if len(line) > 5 and len(line) < 80:
                    # Return cleanly identified title line
                    return line

        return None

