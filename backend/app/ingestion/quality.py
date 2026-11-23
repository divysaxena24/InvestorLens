"""Quality checking for PDF extraction output."""

from __future__ import annotations

import re
from typing import ClassVar, NamedTuple


class QualityCheckResult(NamedTuple):
    quality_flags: list[str]
    review_required: bool


class ExtractionQualityChecker:
    """Evaluates page extraction quality and generates warning flags.

    Quality flags are warnings and heuristics, not automatic proof of
    extraction failure. Legitimate financial figures or sparse pages are
    never rejected solely because a heuristic triggered.
    """

    # Greek characters commonly substituted for digits or symbols in corrupted fonts
    # e.g., ϱ (U+03F1) for 5, ϰ (U+03F0) for 4, ͻ (U+037B), α, β, etc.
    GREEK_DIGIT_SUBSTITUTIONS = re.compile(r"[\u0370-\u03FF]")

    # Common mojibake / encoding corruption artifacts
    ENCODING_CORRUPTIONS: ClassVar[list[str]] = [
        "â€™",
        "â€œ",
        "â€",
        "ï¿½",
        "Ã©",
        "Ã ",
        "Ã¨",
        "Ã´",
        "â€¢",
        "â€“",
        "â€”",
    ]

    # Pattern for suspicious space-separated single digits (e.g., '1 2 3 . 4 5')
    SUSPICIOUS_DIGIT_SPACING = re.compile(r"\b\d(?:\s+\d){3,}\b")

    # Pattern for suspicious broken word spacing (e.g. 'd alo n e', 'Fin an c ial', 'Statemen ts')
    BROKEN_WORD_SPACING = re.compile(r"\b[A-Za-z]{1,3}(?:\s+[A-Za-z]{1,3}){2,}\b")

    def __init__(
        self,
        min_page_chars: int = 40,
        short_page_threshold: int = 150,
    ) -> None:
        self.min_page_chars = min_page_chars
        self.short_page_threshold = short_page_threshold

    def check_page(self, text: str) -> QualityCheckResult:
        flags: list[str] = []
        review_required = False

        stripped = text.strip()
        char_count = len(stripped)

        # 1. Empty or unusually short page checks
        if char_count == 0:
            flags.append("EMPTY_PAGE")
            review_required = True
        elif char_count < self.min_page_chars:
            flags.append("VERY_SHORT_PAGE")
            review_required = True
        elif char_count < self.short_page_threshold:
            flags.append("SHORT_PAGE")

        # 2. Unicode replacement character check
        if "\ufffd" in text:
            replacement_count = text.count("\ufffd")
            flags.append(f"UNICODE_REPLACEMENT_CHAR({replacement_count})")
            review_required = True

        # 3. Encoding corruption check
        found_corruptions = [corrupt for corrupt in self.ENCODING_CORRUPTIONS if corrupt in text]
        if found_corruptions:
            flags.append(f"ENCODING_CORRUPTION({','.join(found_corruptions[:3])})")
            review_required = True

        # 4. Suspicious Greek characters replacing numeric digits / symbols
        greek_matches = self.GREEK_DIGIT_SUBSTITUTIONS.findall(text)
        if greek_matches:
            # Note down unique greek characters
            unique_chars = sorted(set(greek_matches))
            flags.append(f"SUSPICIOUS_GREEK_CHARS({len(greek_matches)}:[{','.join(unique_chars)}])")
            # Greek characters replacing characters in headings or numbers warrants manual review
            review_required = True

        # 5. Suspicious digit spacing
        digit_spacing_matches = self.SUSPICIOUS_DIGIT_SPACING.findall(text)
        if digit_spacing_matches:
            flags.append(f"SUSPICIOUS_DIGIT_SPACING({len(digit_spacing_matches)})")

        # 6. Broken word spacing
        broken_words = self.BROKEN_WORD_SPACING.findall(text)
        if broken_words:
            flags.append(f"BROKEN_WORD_SPACING({len(broken_words)})")

        # 7. Missing or malformed table check
        table_flag = self._check_table_formatting(text)
        if table_flag:
            flags.append(table_flag)
            review_required = True

        return QualityCheckResult(quality_flags=flags, review_required=review_required)

    def _check_table_formatting(self, text: str) -> str | None:
        """Detects if any individual Markdown table has severely mismatched columns.

        Treats separate contiguous table blocks independently rather than flattening
        all tables on the page into one comparison.
        """
        lines = text.splitlines()
        table_blocks: list[list[str]] = []
        current_block: list[str] = []

        for line in lines:
            stripped = line.strip()
            if stripped.startswith("|") and stripped.endswith("|"):
                current_block.append(stripped)
            else:
                if current_block:
                    table_blocks.append(current_block)
                    current_block = []
        if current_block:
            table_blocks.append(current_block)

        if not table_blocks:
            return None

        for b_idx, block in enumerate(table_blocks):
            col_counts: list[int] = []
            for line in block:
                # Ignore separator rows like |---|---|
                if set(line.replace("|", "").strip()) <= {"-", ":", " "}:
                    continue
                cells = [c.strip() for c in line.strip("|").split("|")]
                col_counts.append(len(cells))

            if len(col_counts) >= 2:
                first_cols = col_counts[0]
                mismatched = [count for count in col_counts if count != first_cols]
                # If more than 50% of the rows in this specific table mismatch the header column count
                if len(mismatched) > (len(col_counts) * 0.5):
                    return f"MALFORMED_TABLE(table_{b_idx + 1}_mismatch_{first_cols}_vs_{mismatched[0]})"

        return None

