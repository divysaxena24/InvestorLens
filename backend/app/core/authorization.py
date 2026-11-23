
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.conversation import Conversation
from app.models.document import Document
from app.models.user import User


def get_owned_document(
    document_id: UUID,
    current_user: User,
    db: Session,
) -> Document:
    """Return a document only if it belongs to the authenticated user."""

    statement = select(Document).where(
        Document.id == document_id,
        Document.user_id == current_user.id,
    )

    document = db.scalar(statement)

    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    return document


def get_owned_conversation(
    conversation_id: UUID,
    current_user: User,
    db: Session,
) -> Conversation:
    """Return a conversation only if both it and its document belong to the user."""

    statement = (
        select(Conversation)
        .join(Document, Conversation.document_id == Document.id)
        .where(
            Conversation.id == conversation_id,
            Conversation.user_id == current_user.id,
            Document.user_id == current_user.id,
        )
    )

    conversation = db.scalar(statement)

    if conversation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )

    return conversation
