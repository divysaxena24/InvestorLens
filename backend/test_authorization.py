
import uuid

from fastapi import HTTPException

from app.core.authorization import (
    get_owned_conversation,
    get_owned_document,
)
from app.db.database import SessionLocal
from app.models import Conversation, Document, User

db = SessionLocal()

try:
    # Create two isolated test users
    user_a = User(clerk_user_id=f"test_user_{uuid.uuid4()}")
    user_b = User(clerk_user_id=f"test_user_{uuid.uuid4()}")

    db.add_all([user_a, user_b])
    db.flush()

    # Create a document belonging to User A
    document = Document(
        user_id=user_a.id,
        filename="test_report.pdf",
        storage_key=f"test/{uuid.uuid4()}.pdf",
        file_size_bytes=1024,
    )
    db.add(document)
    db.flush()

    # Create a conversation belonging to User A and their document
    conversation = Conversation(
        user_id=user_a.id,
        document_id=document.id,
        title="Authorization test",
    )
    db.add(conversation)
    db.commit()

    # 1. User A can access their own document
    assert get_owned_document(document.id, user_a, db).id == document.id
    print("PASS: User can access own document")

    # 2. User B cannot access User A's document
    try:
        get_owned_document(document.id, user_b, db)
        raise AssertionError("Unauthorized document access was allowed")
    except HTTPException as exc:
        assert exc.status_code == 404
        print("PASS: Cross-user document access blocked")

    # 3. User A can access their own conversation
    assert get_owned_conversation(
        conversation.id, user_a, db
    ).id == conversation.id
    print("PASS: User can access own conversation")

    # 4. User B cannot access User A's conversation
    try:
        get_owned_conversation(conversation.id, user_b, db)
        raise AssertionError("Unauthorized conversation access was allowed")
    except HTTPException as exc:
        assert exc.status_code == 404
        print("PASS: Cross-user conversation access blocked")

finally:
    # Remove test data
    db.rollback()

    # Delete test records if they were committed
    if "user_a" in locals():
        db.query(User).filter(
            User.clerk_user_id.in_([
                user_a.clerk_user_id,
                user_b.clerk_user_id,
            ])
        ).delete(synchronize_session=False)
        db.commit()

    db.close()
