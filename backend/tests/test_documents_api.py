
from unittest.mock import Mock
from uuid import uuid4

from fastapi import HTTPException

from app.core.deps import get_current_user
from app.main import app
from app.models.document import Document

BASE_URL = "/api/v1/documents"


def create_document(db_session, user_id, storage_key="test-report.pdf"):
    document = Document(
        user_id=user_id,
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


def test_upload_document_success(client, monkeypatch):
    save_mock = Mock(return_value=("uploaded-test.pdf", 2048))
    monkeypatch.setattr(
        "app.api.routes.documents.save_pdf",
        save_mock,
    )

    response = client.post(
        f"{BASE_URL}/upload",
        files={
            "file": (
                "annual-report.pdf",
                b"%PDF-1.4 test content",
                "application/pdf",
            )
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["filename"] == "annual-report.pdf"
    assert data["mime_type"] == "application/pdf"
    assert data["file_size_bytes"] == 2048
    assert data["status"] == "uploaded"
    save_mock.assert_called_once()


def test_list_documents_returns_only_current_users_documents(
    client,
    db_session,
    test_user,
    other_user,
):
    own_document = create_document(
        db_session,
        test_user.id,
        "own-report.pdf",
    )
    create_document(
        db_session,
        other_user.id,
        "other-report.pdf",
    )

    response = client.get(BASE_URL)

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == str(own_document.id)
    assert data[0]["user_id"] == str(test_user.id)


def test_get_document_success(client, db_session, test_user):
    document = create_document(db_session, test_user.id)

    response = client.get(f"{BASE_URL}/{document.id}")

    assert response.status_code == 200
    assert response.json()["id"] == str(document.id)
    assert response.json()["filename"] == "annual-report.pdf"


def test_get_nonexistent_document_returns_404(client):
    response = client.get(f"{BASE_URL}/{uuid4()}")

    assert response.status_code == 404
    assert response.json()["detail"] == "Document not found"


def test_user_cannot_access_another_users_document(
    client,
    db_session,
    other_user,
):
    document = create_document(db_session, other_user.id)

    response = client.get(f"{BASE_URL}/{document.id}")

    assert response.status_code == 404
    assert response.json()["detail"] == "Document not found"


def test_delete_document_success(
    client,
    db_session,
    test_user,
    monkeypatch,
):
    document = create_document(db_session, test_user.id)
    storage_key = document.storage_key

    delete_mock = Mock()
    monkeypatch.setattr(
        "app.api.routes.documents.delete_pdf",
        delete_mock,
    )

    response = client.delete(f"{BASE_URL}/{document.id}")

    assert response.status_code == 204
    assert response.content == b""
    assert db_session.get(Document, document.id) is None
    delete_mock.assert_called_once_with(storage_key)


def test_user_cannot_delete_another_users_document(
    client,
    db_session,
    other_user,
    monkeypatch,
):
    document = create_document(db_session, other_user.id)

    delete_mock = Mock()
    monkeypatch.setattr(
        "app.api.routes.documents.delete_pdf",
        delete_mock,
    )

    response = client.delete(f"{BASE_URL}/{document.id}")

    assert response.status_code == 404
    assert db_session.get(Document, document.id) is not None
    delete_mock.assert_not_called()


def test_deleted_document_cannot_be_retrieved(
    client,
    db_session,
    test_user,
    monkeypatch,
):
    document = create_document(db_session, test_user.id)

    monkeypatch.setattr(
        "app.api.routes.documents.delete_pdf",
        Mock(),
    )

    delete_response = client.delete(f"{BASE_URL}/{document.id}")
    get_response = client.get(f"{BASE_URL}/{document.id}")

    assert delete_response.status_code == 204
    assert get_response.status_code == 404


def test_unauthenticated_request_returns_401(
    client,
    test_user,
):
    app.dependency_overrides.pop(get_current_user)

    try:
        response = client.get(BASE_URL)
    finally:
        app.dependency_overrides[get_current_user] = (
            lambda: test_user
        )

    assert response.status_code == 401
    assert response.json()["detail"] == "Authentication required"


def test_upload_rejects_invalid_pdf(
    client,
    monkeypatch,
):
    def reject_upload(file):
        raise HTTPException(
            status_code=400,
            detail="File does not have a valid PDF signature",
        )

    monkeypatch.setattr(
        "app.api.routes.documents.save_pdf",
        reject_upload,
    )

    response = client.post(
        f"{BASE_URL}/upload",
        files={
            "file": (
                "invalid.pdf",
                b"not a real PDF",
                "application/pdf",
            )
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "File does not have a valid PDF signature"
    )
