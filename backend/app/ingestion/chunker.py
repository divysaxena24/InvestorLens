"""Structure-aware chunking for extracted financial documents."""

from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass, field

from app.ingestion.models import PageExtraction


@dataclass
class DocumentChunk:
    """A searchable chunk with source provenance."""

    chunk_id: str
    document_id: str
    content: str
    page_start: int
    page_end: int
    printed_page: int | None
    section: str | None
    content_type: str
    extraction_method: str
    review_required: bool
    quality_flags: list[str] = field(default_factory=list)


class SemanticChunker:
    """Splits extracted pages while preserving Markdown structure.

    Enforces strict `max_chars` chunk size, safe table splitting with header
    repetition, fallback text splitting for oversized table rows / layout tables,
    and safe overlap handling that never cuts table rows or causes size violations.
    """

    def __init__(
        self,
        max_chars: int = 3200,
        overlap_chars: int = 400,
    ) -> None:
        if max_chars <= 0:
            raise ValueError("max_chars must be positive")
        if overlap_chars < 0 or overlap_chars >= max_chars:
            raise ValueError(
                "overlap_chars must be non-negative and smaller than max_chars"
            )

        self.max_chars = max_chars
        self.overlap_chars = overlap_chars

    @staticmethod
    def _is_table_line(line: str) -> bool:
        stripped = line.strip()
        return stripped.startswith("|") and stripped.endswith("|")

    def _split_blocks(self, text: str) -> list[tuple[str, str]]:
        """Separate contiguous Markdown tables from other content."""
        blocks: list[tuple[str, str]] = []
        current_lines: list[str] = []
        current_type: str | None = None

        for line in text.splitlines():
            line_type = "table" if self._is_table_line(line) else "text"

            if not line.strip():
                if current_lines:
                    blocks.append(
                        (current_type or "text", "\n".join(current_lines).strip())
                    )
                    current_lines = []
                    current_type = None
                continue

            if current_type is not None and line_type != current_type:
                blocks.append((current_type, "\n".join(current_lines).strip()))
                current_lines = []

            current_type = line_type
            current_lines.append(line)

        if current_lines:
            blocks.append((current_type or "text", "\n".join(current_lines).strip()))

        return [(kind, content) for kind, content in blocks if content]

    def _split_text_strict(self, text: str, max_chars: int) -> list[str]:
        """Split text strictly within max_chars without cutting words where possible.

        Splits hierarchically by:
        1. Double newlines (paragraphs)
        2. Sentence boundaries (.!?)
        3. Word boundaries (spaces)
        4. Hard character boundary only if a single word exceeds max_chars.
        """
        text = text.strip()
        if not text:
            return []
        if len(text) <= max_chars:
            return [text]

        paragraphs = text.split("\n\n")
        chunks: list[str] = []
        current_para: list[str] = []
        current_len = 0

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            if len(para) > max_chars:
                if current_para:
                    chunks.append("\n\n".join(current_para))
                    current_para = []
                    current_len = 0

                sentences = re.split(r"(?<=[.!?])\s+", para)
                for s in sentences:
                    s = s.strip()
                    if not s:
                        continue

                    if len(s) > max_chars:
                        if current_para:
                            chunks.append("\n\n".join(current_para))
                            current_para = []
                            current_len = 0

                        words = s.split(" ")
                        for w in words:
                            if not w:
                                continue
                            if len(w) > max_chars:
                                if current_para:
                                    chunks.append(" ".join(current_para))
                                    current_para = []
                                    current_len = 0
                                for i in range(0, len(w), max_chars):
                                    chunks.append(w[i : i + max_chars])
                            else:
                                cand_len = current_len + (1 if current_para else 0) + len(w)
                                if cand_len <= max_chars:
                                    current_para.append(w)
                                    current_len = cand_len
                                else:
                                    chunks.append(" ".join(current_para))
                                    current_para = [w]
                                    current_len = len(w)
                        if current_para:
                            chunks.append(" ".join(current_para))
                            current_para = []
                            current_len = 0
                    else:
                        cand_len = current_len + (2 if current_para else 0) + len(s)
                        if cand_len <= max_chars:
                            current_para.append(s)
                            current_len = cand_len
                        else:
                            chunks.append("\n\n".join(current_para))
                            current_para = [s]
                            current_len = len(s)
            else:
                cand_len = current_len + (2 if current_para else 0) + len(para)
                if cand_len <= max_chars:
                    current_para.append(para)
                    current_len = cand_len
                else:
                    chunks.append("\n\n".join(current_para))
                    current_para = [para]
                    current_len = len(para)

        if current_para:
            chunks.append("\n\n".join(current_para))

        return chunks

    def _split_oversized_row(self, row: str, max_chars: int) -> list[str]:
        """Safely unpacks a single oversized table row into formatted text blocks.

        Preserves all cell text without creating oversized chunks.
        """
        cells = [c.strip() for c in row.strip("|").split("|")]
        cell_texts = [c.replace("<br>", "\n").strip() for c in cells if c.strip()]
        combined = "\n\n".join(cell_texts)
        return self._split_text_strict(combined, max_chars)

    def _split_table(self, table: str) -> list[tuple[str, str]]:
        """Splits tables by rows while repeating the header when valid.

        Handles:
        1. Conventional tables with headers and separators: repeats header per chunk.
        2. Single oversized row (e.g. AGM / e-voting layout tables): unpacks into text.
        3. Header exceeding max_chars: safely converts entire table to text chunks.
        """
        lines = [line for line in table.splitlines() if line.strip()]
        if not lines:
            return []

        has_header = False
        header_lines: list[str] = []
        data_rows: list[str] = []

        if len(lines) >= 2:
            sep = lines[1].replace("|", "").strip()
            if set(sep) <= {"-", ":", " "} and len(sep) > 0:
                has_header = True
                header_lines = lines[:2]
                data_rows = lines[2:]
            else:
                data_rows = lines
        else:
            data_rows = lines

        header_block = "\n".join(header_lines) if has_header else ""
        header_len = len(header_block)

        # If header itself exceeds max_chars, fallback entire table as text
        if has_header and header_len >= self.max_chars:
            raw_text = "\n".join(lines).replace("<br>", "\n").replace("|", " ")
            return [("text", p) for p in self._split_text_strict(raw_text, self.max_chars)]

        results: list[tuple[str, str]] = []
        current_rows: list[str] = []

        for row in data_rows:
            # Check if this row cannot fit alongside the repeated header
            min_cand_len = header_len + (1 if has_header else 0) + len(row)
            if min_cand_len > self.max_chars:
                if current_rows:
                    if has_header:
                        results.append(("table", "\n".join(header_lines + current_rows)))
                    else:
                        results.append(("table", "\n".join(current_rows)))
                    current_rows = []

                if len(row) > self.max_chars:
                    # Single row exceeds max_chars: safe fallback unpack to text blocks
                    row_parts = self._split_oversized_row(row, self.max_chars)
                    for part in row_parts:
                        results.append(("text", part))
                else:
                    # Row fits standalone within max_chars without header repetition
                    results.append(("table", row))
                continue

            candidate_lines = (header_lines if has_header else []) + current_rows + [row]
            candidate_text = "\n".join(candidate_lines)

            if len(candidate_text) <= self.max_chars:
                current_rows.append(row)
            else:
                if current_rows:
                    if has_header:
                        results.append(("table", "\n".join(header_lines + current_rows)))
                    else:
                        results.append(("table", "\n".join(current_rows)))
                current_rows = [row]

        if current_rows:
            if has_header:
                results.append(("table", "\n".join(header_lines + current_rows)))
            else:
                results.append(("table", "\n".join(current_rows)))

        return results

    def _prepare_blocks(self, text: str) -> list[tuple[str, str]]:
        """Prepares and decomposes blocks so every single block fits within max_chars."""
        prepared: list[tuple[str, str]] = []

        for kind, content in self._split_blocks(text):
            if len(content) <= self.max_chars:
                if kind == "table":
                    # Check if any single line in the table exceeds max_chars
                    lines = [l for l in content.splitlines() if l.strip()]
                    if any(len(l) > self.max_chars for l in lines):
                        prepared.extend(self._split_table(content))
                    else:
                        prepared.append((kind, content))
                else:
                    prepared.append((kind, content))
            elif kind == "table":
                prepared.extend(self._split_table(content))
            else:
                prepared.extend(
                    ("text", part) for part in self._split_text_strict(content, self.max_chars)
                )

        return prepared

    def chunk_pages(
        self,
        pages: Sequence[PageExtraction],
        document_id: str,
    ) -> list[DocumentChunk]:
        """Convert extracted pages into provenance-preserving chunks.

        Pages are processed independently. Chunks never cross page boundaries.
        Overlaps are restricted to text-to-text boundaries and never cut through table rows
        or cause chunk length to exceed max_chars.
        """
        if not document_id.strip():
            raise ValueError("document_id cannot be empty")

        result: list[DocumentChunk] = []

        for page in pages:
            if not page.text.strip():
                continue

            blocks = self._prepare_blocks(page.text)

            current_blocks: list[tuple[str, str]] = []
            current_length = 0
            page_chunks: list[tuple[str, str]] = []

            for kind, content in blocks:
                separator_length = 2 if current_blocks else 0
                candidate_length = (
                    current_length + separator_length + len(content)
                )

                if current_blocks and candidate_length > self.max_chars:
                    combined = "\n\n".join(
                        block for _, block in current_blocks
                    )
                    combined_type = (
                        "table"
                        if all(k == "table" for k, _ in current_blocks)
                        else "text"
                    )
                    page_chunks.append((combined_type, combined))

                    # Disable overlap if either previous chunk or current block contains table.
                    # This prevents cutting table rows and malformed syntax.
                    prev_has_table = any(k == "table" for k, _ in current_blocks)
                    curr_is_table = (kind == "table")

                    current_blocks = []
                    current_length = 0

                    if self.overlap_chars and not prev_has_table and not curr_is_table:
                        tail = combined[-self.overlap_chars :]
                        space_idx = tail.find(" ")
                        if space_idx != -1 and space_idx < len(tail) - 1:
                            tail = tail[space_idx + 1 :].strip()

                        # Ensure adding overlap does not cause subsequent chunk to exceed max_chars
                        if tail and (len(tail) + 2 + len(content)) <= self.max_chars:
                            current_blocks.append(("text", tail))
                            current_length = len(tail)

                current_blocks.append((kind, content))
                current_length = len("\n\n".join(b for _, b in current_blocks))

            if current_blocks:
                combined = "\n\n".join(
                    block for _, block in current_blocks
                )
                combined_type = (
                    "table"
                    if all(k == "table" for k, _ in current_blocks)
                    else "text"
                )
                page_chunks.append((combined_type, combined))

            for index, (content_type, content) in enumerate(
                page_chunks, start=1
            ):
                result.append(
                    DocumentChunk(
                        chunk_id=f"{document_id}_p{page.pdf_page}_{index:03d}",
                        document_id=document_id,
                        content=content,
                        page_start=page.pdf_page,
                        page_end=page.pdf_page,
                        printed_page=page.printed_page,
                        section=page.section,
                        content_type=content_type,
                        extraction_method=page.extraction_method,
                        review_required=page.review_required,
                        quality_flags=list(page.quality_flags),
                    )
                )

        return result
