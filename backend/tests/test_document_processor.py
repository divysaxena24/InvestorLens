
import json
from threading import Event, Thread
from types import SimpleNamespace
from uuid import uuid4

import numpy as np
import pytest
from sqlalchemy.orm import Session

from app.ingestion.chunker import DocumentChunk
from app.models.document import Document
from app.services import document_processor


@pytest.fixture
def processor_db(db_session, monkeypatch):
    """Give the processor an independent session using the test database."""

    monkeypatch.setattr(
        "app.services.document_processor.SessionLocal",
        lambda: Session(bind=db_session.get_bind()),
    )
    return db_session


def create_test_document(db_session, storage_key="test-report.pdf"):
    """Create a document with its required user."""

    from app.models.user import User

    user = User(
        clerk_user_id=f"clerk_{uuid4()}",
        email=f"{uuid4()}@example.com",
        full_name="Processor Test User",
    )

    db_session.add(user)
    db_session.flush()

    document = Document(
        user_id=user.id,
        filename="annual-report.pdf",
        storage_key=storage_key,
        mime_type="application/pdf",
        file_size_bytes=1024,
        status="uploaded",
    )

    db_session.add(document)
    db_session.commit()
    db_session.refresh(document)

    return document


class FakeChunker:
    """Generate a realistic chunk without running the actual chunker."""

    def chunk_pages(self, pages, document_id):
        return [
            DocumentChunk(
                chunk_id=f"{document_id}_chunk_1",
                document_id=document_id,
                content="This is a test financial report.",
                page_start=1,
                page_end=1,
                printed_page=None,
                section="Financial Overview",
                content_type="text",
                extraction_method="native",
                review_required=False,
                quality_flags=[],
            )
        ]


class FakeEmbeddingGenerator:
    """Generate a normalized 384-dimensional test embedding."""

    def generate(self, texts):
        assert len(texts) == 1

        vector = np.zeros(384, dtype=np.float32)
        vector[0] = 1.0

        return [vector.tolist()]


def test_process_document_success(
    processor_db,
    monkeypatch,
    tmp_path,
):
    document = create_test_document(processor_db)

    upload_dir = tmp_path / "uploads"
    processed_dir = tmp_path / "processed"

    upload_dir.mkdir()
    (upload_dir / document.storage_key).write_bytes(b"%PDF-test")

    monkeypatch.setattr(
        document_processor,
        "UPLOAD_DIR",
        upload_dir,
    )
    monkeypatch.setattr(
        document_processor,
        "PROCESSED_DIR",
        processed_dir,
    )

    class FakePipeline:
        def extract_native(self, pdf_path, progress_callback=None):
            assert pdf_path.is_file()

            if progress_callback:
                progress_callback(1, 1)

            return [SimpleNamespace(pdf_page=1)]

        def save_markdown(self, pages, output_path):
            output_path.write_text(
                "# Extracted report\nTest content",
                encoding="utf-8",
            )
            return output_path

        def save_quality_report(self, pages, output_path):
            output_path.write_text(
                "page,quality\n1,passed",
                encoding="utf-8",
            )
            return output_path

    monkeypatch.setattr(
        document_processor,
        "PDFExtractionPipeline",
        FakePipeline,
    )
    monkeypatch.setattr(
        document_processor,
        "SemanticChunker",
        FakeChunker,
    )
    monkeypatch.setattr(
        document_processor,
        "EmbeddingGenerator",
        FakeEmbeddingGenerator,
    )

    # Mock Qdrant so the test does not require a running server.
    qdrant_calls = []
    client_closed = []

    class FakeQdrantClient:
        def close(self):
            client_closed.append(True)

    def fake_upsert(**kwargs):
        qdrant_calls.append(kwargs)
        return len(kwargs["chunks"])

    monkeypatch.setattr(
        document_processor,
        "get_qdrant_client",
        lambda: FakeQdrantClient(),
    )
    monkeypatch.setattr(
        document_processor,
        "upsert_document_chunks",
        fake_upsert,
    )

    document_processor.process_document(
        str(document.id),
        document.storage_key,
    )

    processor_db.expire_all()
    updated_document = processor_db.get(Document, document.id)

    output_dir = processed_dir / str(document.id)

    # Verify processing status.
    assert updated_document.status == "processed"

    # Verify extraction artifacts.
    assert (output_dir / "extracted.md").is_file()
    assert (output_dir / "quality_report.csv").is_file()

    # Verify embedding artifacts.
    vectors_path = output_dir / "document_vectors.npz"
    chunks_path = output_dir / "document_chunks.json"

    assert vectors_path.is_file()
    assert chunks_path.is_file()

    # Verify embedding dimensions.
    saved_vectors = np.load(vectors_path)["vectors"]
    assert saved_vectors.shape == (1, 384)

    # Verify chunk metadata.
    saved_chunks = json.loads(
        chunks_path.read_text(encoding="utf-8")
    )

    assert len(saved_chunks) == 1
    assert saved_chunks[0]["content"] == (
        "This is a test financial report."
    )
    assert saved_chunks[0]["document_id"] == str(document.id)

    # Verify Qdrant indexing.
    assert len(qdrant_calls) == 1

    qdrant_call = qdrant_calls[0]

    assert qdrant_call["document_id"] == str(document.id)
    assert qdrant_call["user_id"] == str(document.user_id)
    assert len(qdrant_call["chunks"]) == 1
    assert qdrant_call["vectors"].shape == (1, 384)

    # Verify client cleanup.
    assert client_closed == [True]


def test_process_document_failure_marks_document_failed(
    processor_db,
    monkeypatch,
    tmp_path,
):
    document = create_test_document(processor_db)

    upload_dir = tmp_path / "uploads"
    processed_dir = tmp_path / "processed"

    upload_dir.mkdir()
    (upload_dir / document.storage_key).write_bytes(b"%PDF-test")

    monkeypatch.setattr(
        document_processor,
        "UPLOAD_DIR",
        upload_dir,
    )
    monkeypatch.setattr(
        document_processor,
        "PROCESSED_DIR",
        processed_dir,
    )

    class FailingPipeline:
        def extract_native(self, pdf_path, progress_callback=None):
            raise RuntimeError("Simulated extraction failure")

    monkeypatch.setattr(
        document_processor,
        "PDFExtractionPipeline",
        FailingPipeline,
    )

    document_processor.process_document(
        str(document.id),
        document.storage_key,
    )

    processor_db.expire_all()
    updated_document = processor_db.get(Document, document.id)

    assert updated_document.status == "failed"


def test_process_document_embedding_validation_failure(
    processor_db,
    monkeypatch,
    tmp_path,
):
    document = create_test_document(processor_db)

    upload_dir = tmp_path / "uploads"
    processed_dir = tmp_path / "processed"

    upload_dir.mkdir()
    (upload_dir / document.storage_key).write_bytes(b"%PDF-test")

    monkeypatch.setattr(
        document_processor,
        "UPLOAD_DIR",
        upload_dir,
    )
    monkeypatch.setattr(
        document_processor,
        "PROCESSED_DIR",
        processed_dir,
    )

    class FakePipeline:
        def extract_native(self, pdf_path, progress_callback=None):
            return [SimpleNamespace(pdf_page=1)]

        def save_markdown(self, pages, output_path):
            output_path.write_text(
                "# Extracted report",
                encoding="utf-8",
            )
            return output_path

        def save_quality_report(self, pages, output_path):
            output_path.write_text(
                "page,quality\n1,passed",
                encoding="utf-8",
            )
            return output_path

    class InvalidEmbeddingGenerator:
        def generate(self, texts):
            # Wrong dimension: expected 384.
            return [[0.1, 0.2, 0.3]]

    monkeypatch.setattr(
        document_processor,
        "PDFExtractionPipeline",
        FakePipeline,
    )
    monkeypatch.setattr(
        document_processor,
        "SemanticChunker",
        FakeChunker,
    )
    monkeypatch.setattr(
        document_processor,
        "EmbeddingGenerator",
        InvalidEmbeddingGenerator,
    )

    document_processor.process_document(
        str(document.id),
        document.storage_key,
    )

    processor_db.expire_all()
    updated_document = processor_db.get(Document, document.id)

    output_dir = processed_dir / str(document.id)

    assert updated_document.status == "failed"
    assert not (output_dir / "document_vectors.npz").exists()
    assert not (output_dir / "document_chunks.json").exists()


def test_process_document_missing_pdf_marks_document_failed(
    processor_db,
    monkeypatch,
    tmp_path,
):
    document = create_test_document(processor_db)

    monkeypatch.setattr(
        document_processor,
        "UPLOAD_DIR",
        tmp_path / "missing_uploads",
    )
    monkeypatch.setattr(
        document_processor,
        "PROCESSED_DIR",
        tmp_path / "processed",
    )

    document_processor.process_document(
        str(document.id),
        document.storage_key,
    )

    processor_db.expire_all()
    updated_document = processor_db.get(Document, document.id)

    assert updated_document.status == "failed"


def test_process_document_missing_database_record(processor_db):
    """Missing database records should exit safely."""

    document_processor.process_document(
        str(uuid4()),
        "missing.pdf",
    )


def test_delete_processed_artifacts_removes_directory(
    monkeypatch,
    tmp_path,
):
    document_id = str(uuid4())
    processed_dir = tmp_path / document_id
    processed_dir.mkdir()

    (processed_dir / "extracted.md").write_text(
        "# Financial report",
        encoding="utf-8",
    )
    (processed_dir / "quality_report.csv").write_text(
        "page,quality\n1,passed",
        encoding="utf-8",
    )

    monkeypatch.setattr(
        document_processor,
        "PROCESSED_DIR",
        tmp_path,
    )

    document_processor.delete_processed_artifacts(document_id)

    assert not processed_dir.exists()


def test_delete_processed_artifacts_handles_missing_directory(
    monkeypatch,
    tmp_path,
):
    document_id = str(uuid4())

    monkeypatch.setattr(
        document_processor,
        "PROCESSED_DIR",
        tmp_path,
    )

    # Repeated cleanup should be safe.
    document_processor.delete_processed_artifacts(document_id)
    document_processor.delete_processed_artifacts(document_id)

    assert not (tmp_path / document_id).exists()


def test_process_document_waits_for_deletion_lock(monkeypatch):
    document_id = str(uuid4())
    storage_key = "test-report.pdf"

    lock = document_processor.get_document_lock(document_id)

    attempted = Event()
    finished = Event()
    calls = []

    def fake_process(document_id, storage_key):
        calls.append((document_id, storage_key))

    monkeypatch.setattr(
        document_processor,
        "_process_document",
        fake_process,
    )

    def worker():
        attempted.set()
        document_processor.process_document(
            document_id,
            storage_key,
        )
        finished.set()

    with lock:
        thread = Thread(target=worker)
        thread.start()

        assert attempted.wait(timeout=2)

        # Processing must wait while deletion owns the lock.
        assert not finished.wait(timeout=0.2)

    # Once deletion releases the lock, processing can continue.
    assert finished.wait(timeout=2)

    thread.join(timeout=2)

    assert not thread.is_alive()
    assert calls == [(document_id, storage_key)]
