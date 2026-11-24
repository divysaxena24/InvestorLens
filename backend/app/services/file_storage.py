
import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile, status

# backend/storage/uploads/
BACKEND_DIR = Path(__file__).resolve().parents[2]
UPLOAD_DIR = BACKEND_DIR / "storage" / "uploads"

MAX_FILE_SIZE = 25 * 1024 * 1024  # 25 MB
CHUNK_SIZE = 1024 * 1024  # 1 MB


def save_pdf(upload: UploadFile) -> tuple[str, int]:
    """
    Save an uploaded PDF using a generated UUID filename.

    Returns:
        (storage_key, file_size_bytes)
    """
    if not upload.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename is required",
        )

    if Path(upload.filename).suffix.lower() != ".pdf":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are allowed",
        )

    if upload.content_type != "application/pdf":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid content type. Upload a PDF.",
        )

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    storage_key = f"{uuid.uuid4()}.pdf"
    destination = UPLOAD_DIR / storage_key
    file_size = 0

    try:
        with destination.open("xb") as output:
            while chunk := upload.file.read(CHUNK_SIZE):
                file_size += len(chunk)

                if file_size > MAX_FILE_SIZE:
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail="PDF exceeds the 25 MB upload limit",
                    )

                output.write(chunk)

        if file_size == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded PDF is empty",
            )

        # Verify PDF signature (basic file validation).
        with destination.open("rb") as saved_file:
            if saved_file.read(5) != b"%PDF-":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="File does not have a valid PDF signature",
                )

        return storage_key, file_size

    except Exception:
        destination.unlink(missing_ok=True)
        raise


def delete_pdf(storage_key: str) -> None:
    """Delete a stored PDF safely."""
    if Path(storage_key).name != storage_key:
        raise ValueError("Invalid storage key")

    if not storage_key.endswith(".pdf"):
        raise ValueError("Invalid storage key")

    destination = UPLOAD_DIR / storage_key
    destination.unlink(missing_ok=True)
