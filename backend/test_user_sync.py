import os

from fastapi.security import HTTPAuthorizationCredentials

from app.core.deps import get_current_user
from app.db.database import SessionLocal

token = os.getenv("CLERK_TEST_TOKEN")

if not token:
    raise RuntimeError("CLERK_TEST_TOKEN is missing")

credentials = HTTPAuthorizationCredentials(
    scheme="Bearer",
    credentials=token,
)

db = SessionLocal()

try:
    # First call: create the user if not already present
    user1 = get_current_user(credentials=credentials, db=db)

    print("Authenticated user lookup successful")
    print("Internal user ID present:", user1.id is not None)

    # Second call: retrieve the existing user
    user2 = get_current_user(credentials=credentials, db=db)

    print("Existing user retrieved:", user1.id == user2.id)
    print("User record persisted:", db.get(type(user1), user1.id) is not None)

finally:
    db.close()