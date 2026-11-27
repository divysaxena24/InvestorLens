
"""Background processing for uploaded financial documents."""

import logging
import shutil
from threading import RLock
from uuid import UUID

import numpy as np
from sqlalchemy import select

from app.db.database import SessionLocal
from app.ingestion.artifacts import (
    save_embeddings_and_metadata,
    validate_embeddings,
)
from app.ingestion.chunker import SemanticChunker
from app.ingestion.embeddings import EmbeddingGenerator
from app.ingestion.extractor import PDFExtractionPipeline
from app.models.document import Document
from app.services.file_storage import BACKEND_DIR, UPLOAD_DIR

logger = logging.getLogger(__name__)

PROCESSED_DIR = BACKEND_DIR / "storage" / "processed"

# Per-document locks coordinate processing and deletion within this process.
_lock_registry_guard = RLock()
_document_locks: dict[str, RLock] = {}


def get_document_lock(document_id: str) -> RLock:
    """Return the shared lock for a document."""

    safe_document_id = str(UUID(document_id))

    with _lock_registry_guard:
        if safe_document_id not in _document_locks:
            _document_locks[safe_document_id] = RLock()

        return _document_locks[safe_document_id]


def process_document(document_id: str, storage_key: str) -> None:
    """Process an uploaded PDF while holding its document lock."""

    safe_document_id = str(UUID(document_id))

    with get_document_lock(safe_document_id):
        _process_document(safe_document_id, storage_key)


def _process_document(
    document_id: str,
    storage_key: str,
    chunker: SemanticChunker | None = None,
    embedding_generator: EmbeddingGenerator | None = None,
) -> None:
    """Extract, chunk, embed, validate, and persist a document."""

    db = SessionLocal()

    try:
        document = db.scalar(
            select(Document).where(Document.id == UUID(document_id))
        )

        if document is None:
            logger.warning(
                "Document %s no longer exists; skipping processing",
                document_id,
            )
            return

        document.status = "processing"
        db.commit()

        pdf_path = UPLOAD_DIR / storage_key

        if not pdf_path.is_file():
            raise FileNotFoundError(
                f"Uploaded PDF not found: {storage_key}"
            )

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

        # Stage 1: Extract PDF pages.
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

        # Stage 2: Generate structure-aware chunks.
        chunker = chunker or SemanticChunker()

        chunks = chunker.chunk_pages(
            pages,
            document_id=document_id,
        )

        if not chunks:
            raise ValueError("No chunks could be generated from the PDF")

        logger.info(
            "Document %s: generated %d chunks",
            document_id,
            len(chunks),
        )

        # Stage 3: Generate embeddings.
        embedding_generator = embedding_generator or EmbeddingGenerator()

        vectors = np.asarray(
            embedding_generator.generate(
                [chunk.content for chunk in chunks]
            ),
            dtype=np.float32,
        )

        # Stage 4: Validate embeddings and metadata.
        validation = validate_embeddings(chunks, vectors)

        failed_checks = [
            check
            for check, passed in validation.items()
            if not passed
        ]

        if failed_checks:
            raise ValueError(
                f"Embedding validation failed: {', '.join(failed_checks)}"
            )

        logger.info(
            "Document %s: generated %d embeddings (%d dimensions)",
            document_id,
            len(vectors),
            vectors.shape[1],
        )

        # Stage 5: Persist vectors and chunk metadata.
        save_embeddings_and_metadata(
            chunks=chunks,
            vectors=vectors,
            output_dir=output_dir,
            stem="document",
        )

        # Mark processed only after all stages succeed.
        document.status = "processed"
        db.commit()

        logger.info(
            "Document %s processed successfully: %d pages, %d chunks",
            document_id,
            len(pages),
            len(chunks),
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


def delete_processed_artifacts(document_id: str) -> None:
    """Delete all generated files for a document."""

    safe_document_id = str(UUID(document_id))

    with get_document_lock(safe_document_id):
        output_dir = PROCESSED_DIR / safe_document_id

        if output_dir.is_dir():
            shutil.rmtree(output_dir)

        logger.info(
            "Processed artifacts deleted for document %s",
            safe_document_id,
        )
