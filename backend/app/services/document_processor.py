
"""Background processing for uploaded financial documents."""

import logging
from uuid import UUID

from sqlalchemy import select

from app.db.database import SessionLocal
from app.ingestion.extractor import PDFExtractionPipeline
from app.models.document import Document
from app.services.file_storage import BACKEND_DIR, UPLOAD_DIR

logger = logging.getLogger(__name__)

PROCESSED_DIR = BACKEND_DIR / "storage" / "processed"


def process_document(document_id: str, storage_key: str) -> None:
    """Extract an uploaded PDF and save its Markdown and quality report."""

    db = SessionLocal()

    try:
        document = db.scalar(
            select(Document).where(Document.id == UUID(document_id))
        )

        # The user may have deleted the document before processing started.
        if document is None:
            logger.warning("Document %s no longer exists", document_id)
            return

        document.status = "processing"
        db.commit()

        pdf_path = UPLOAD_DIR / storage_key

        if not pdf_path.is_file():
            raise FileNotFoundError(f"Uploaded PDF not found: {storage_key}")

        output_dir = PROCESSED_DIR / document_id
        output_dir.mkdir(parents=True, exist_ok=True)

        pipeline = PDFExtractionPipeline()

        def progress(current: int, total: int) -> None:
            if current % 25 == 0 or current == total:
                logger.info(
                    "Document %s: extracted %d/%d pages",
                    document_id,
                    current,
                    total,
                )

        pages = pipeline.extract_native(
            pdf_path,
            progress_callback=progress,
        )

        if not pages:
            raise ValueError("No pages could be extracted from the PDF")

        pipeline.save_markdown(
            pages,
            output_dir / "extracted.md",
        )

        pipeline.save_quality_report(
            pages,
            output_dir / "quality_report.csv",
        )

        document.status = "processed"
        db.commit()

        logger.info(
            "Document %s processed successfully: %d pages",
            document_id,
            len(pages),
        )

    except Exception:
        db.rollback()
        logger.exception("Document processing failed: %s", document_id)

        try:
            document = db.scalar(
                select(Document).where(Document.id == UUID(document_id))
            )

            if document is not None:
                document.status = "failed"
                db.commit()

        except Exception:
            db.rollback()
            logger.exception(
                "Could not update failure status for document %s",
                document_id,
            )

    finally:
        db.close()
