"""CSV report generation for extraction quality and audit."""

from __future__ import annotations

import csv
from collections.abc import Sequence
from pathlib import Path

from app.ingestion.models import PageExtraction, QualityReportRow


def generate_quality_report(
    pages: Sequence[PageExtraction],
    output_csv_path: Path,
) -> Path:
    """Generates a CSV report with columns:

    pdf_page, printed_page, section, extraction_method, characters, review_required, quality_flags
    """
    output_csv_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "pdf_page",
        "printed_page",
        "section",
        "extraction_method",
        "characters",
        "review_required",
        "quality_flags",
    ]

    with open(output_csv_path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for page in pages:
            row = QualityReportRow(
                pdf_page=page.pdf_page,
                printed_page=page.printed_page,
                section=page.section,
                extraction_method=page.extraction_method,
                characters=page.character_count,
                review_required=page.review_required,
                quality_flags="; ".join(page.quality_flags) if page.quality_flags else "NONE",
            )
            writer.writerow(row.to_csv_dict())

    return output_csv_path

