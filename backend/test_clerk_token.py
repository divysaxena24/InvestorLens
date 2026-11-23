import os

from app.core.security import verify_clerk_token

token = os.getenv("CLERK_TEST_TOKEN")

if not token:
    raise RuntimeError("CLERK_TEST_TOKEN is missing")

claims = verify_clerk_token(token)

print("Clerk JWT verification successful")
print("Subject present:", bool(claims.get("sub")))
print("Issuer:", claims.get("iss"))
print("Expiration present:", bool(claims.get("exp")))