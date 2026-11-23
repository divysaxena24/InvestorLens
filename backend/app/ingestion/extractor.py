"""PDF extraction pipeline orchestrator.

Extracts PDF to Markdown, preserves page metadata, performs extraction quality checks,
and supports selective OCR evaluation without modifying the original PDF or forcing full OCR.
"""

from __future__ import annotations

import logging
from collections.abc import Callable, Sequence
from pathlib import Path

import pymupdf
import pymupdf4llm

from app.ingestion.compare import compare_extractions
from app.ingestion.metadata import MetadataExtractor
from app.ingestion.models import PageComparison, PageExtraction
from app.ingestion.quality import ExtractionQualityChecker
from app.ingestion.report import generate_quality_report

logger = logging.getLogger(__name__)


class PDFExtractionPipeline:
    """End-to-end pipeline for validated PDF extraction."""

    def __init__(
        self,
        quality_checker: ExtractionQualityChecker | None = None,
        metadata_extractor: MetadataExtractor | None = None,
    ) -> None:
        self.quality_checker = quality_checker or ExtractionQualityChecker()
        self.metadata_extractor = metadata_extractor or MetadataExtractor()

    def extract_native(
        self,
        pdf_path: Path,
        pages: Sequence[int] | None = None,
        progress_callback: Callable[[int, int], None] | None = None,
    ) -> list[PageExtraction]:
        """Extracts pages using native extraction (pymupdf4llm).

        pages: list of 1-based page numbers to extract. If None, extracts all pages.
        Never overwrites or modifies the original PDF.
        """
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        doc = pymupdf.open(pdf_path)
        total_pdf_pages = len(doc)

        # Convert 1-based requested pages to zero-based for pymupdf4llm
        if pages is not None:
            target_1based = [p for p in pages if 1 <= p <= total_pdf_pages]
            target_0based = [p - 1 for p in target_1based]
        else:
            target_1based = list(range(1, total_pdf_pages + 1))
            target_0based = list(range(total_pdf_pages))

        logger.info(
            f"Extracting {len(target_0based)} pages natively from {pdf_path.name}"
        )

        # pymupdf4llm page chunks
        chunks = pymupdf4llm.to_markdown(
            str(pdf_path),
            pages=target_0based,
            page_chunks=True,
        )

        extracted_pages: list[PageExtraction] = []

        for idx, (p_1based, chunk) in enumerate(zip(target_1based, chunks)):
            text = chunk.get("text", "")

            # Extract metadata from actual page object
            fitz_page = doc[p_1based - 1]
            printed_page, section = self.metadata_extractor.extract_page_metadata(
                fitz_page, p_1based
            )

            # Perform quality checks
            quality_result = self.quality_checker.check_page(text)

            page_ext = PageExtraction(
                pdf_page=p_1based,
                printed_page=printed_page,
                section=section,
                text=text,
                extraction_method="native",
                review_required=quality_result.review_required,
                quality_flags=quality_result.quality_flags,
            )
            extracted_pages.append(page_ext)

            if progress_callback:
                progress_callback(idx + 1, len(target_1based))

        doc.close()
        return extracted_pages

    def extract_ocr_selective(
        self,
        pdf_path: Path,
        selected_pages: Sequence[int],
    ) -> list[PageExtraction]:
        """Extracts selected pages using OCR (force_ocr=True with rapidocr).

        selected_pages: sequence of 1-based PDF page numbers.
        Avoids forcing OCR across all pages.
        """
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        doc = pymupdf.open(pdf_path)
        total_pdf_pages = len(doc)

        target_1based = [p for p in selected_pages if 1 <= p <= total_pdf_pages]
        if not target_1based:
            doc.close()
            return []

        target_0based = [p - 1 for p in target_1based]

        logger.info(
            f"Running selective OCR on {len(target_0based)} pages: {target_1based}"
        )

        chunks = pymupdf4llm.to_markdown(
            str(pdf_path),
            pages=target_0based,
            page_chunks=True,
            force_ocr=True,
        )

        ocr_pages: list[PageExtraction] = []

        for p_1based, chunk in zip(target_1based, chunks):
            text = chunk.get("text", "")
            fitz_page = doc[p_1based - 1]
            printed_page, section = self.metadata_extractor.extract_page_metadata(
                fitz_page, p_1based
            )

            quality_result = self.quality_checker.check_page(text)

            ocr_ext = PageExtraction(
                pdf_page=p_1based,
                printed_page=printed_page,
                section=section,
                text=text,
                extraction_method="ocr",
                review_required=quality_result.review_required,
                quality_flags=quality_result.quality_flags,
            )
            ocr_pages.append(ocr_ext)

        doc.close()
        return ocr_pages

    def compare_page(
        self,
        native_page: PageExtraction,
        ocr_page: PageExtraction,
    ) -> PageComparison:
        """Compares native extraction against OCR extraction for a given page."""
        return compare_extractions(native_page, ocr_page)

    def save_markdown(
        self,
        pages: Sequence[PageExtraction],
        output_path: Path,
    ) -> Path:
        """Saves page extractions as a Markdown file with page boundary markers."""
        output_path.parent.mkdir(parents=True, exist_ok=True)

        parts: list[str] = []
        for p in pages:
            header_meta = [f"Page {p.pdf_page}"]
            if p.printed_page is not None:
                header_meta.append(f"Printed: {p.printed_page}")
            if p.section:
                header_meta.append(f"Section: {p.section}")
            header_meta.append(f"Method: {p.extraction_method}")

            comment = f"<!-- {' | '.join(header_meta)} -->"
            parts.append(f"\n\n{comment}\n\n{p.text}")

        markdown_content = "\n".join(parts).lstrip()
        output_path.write_text(markdown_content, encoding="utf-8")
        return output_path

    def save_quality_report(
        self,
        pages: Sequence[PageExtraction],
        output_csv_path: Path,
    ) -> Path:
        """Saves the extraction quality CSV report."""
        return generate_quality_report(pages, output_csv_path)

