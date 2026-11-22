from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from app.core.deps import get_current_user
from app.db.database import SessionLocal

db = SessionLocal()

try:
    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials="invalid.token.value",
    )

    get_current_user(credentials=credentials, db=db)

except HTTPException as error:
    print("Status:", error.status_code)
    print("Detail:", error.detail)

finally:
    db.close()