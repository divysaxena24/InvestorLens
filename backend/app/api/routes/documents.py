
import logging

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    UploadFile,
    status,
)
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db.database import get_db
from app.models.document import Document
from app.models.user import User
from app.schemas.document import DocumentResponse
from app.services.file_storage import save_pdf, delete_pdf

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post(
    "/upload",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
)
def upload_document(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    storage_key, file_size = save_pdf(file)

    try:
        document = Document(
            user_id=current_user.id,
            filename=file.filename,
            storage_key=storage_key,
            mime_type="application/pdf",
            file_size_bytes=file_size,
            status="uploaded",
        )

        db.add(document)
        db.commit()
        db.refresh(document)

        return document

    except Exception:
        logger.exception("Document upload failed")
        db.rollback()
        delete_pdf(storage_key)

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not save document metadata",
        )

    finally:
        file.file.close()
