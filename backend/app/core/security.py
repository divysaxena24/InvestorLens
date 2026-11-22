import jwt
from jwt import PyJWKClient
from jwt.exceptions import PyJWKClientError, PyJWTError
from fastapi import HTTPException, status

from app.core.config import settings


# Clerk's public JSON Web Key Set endpoint
JWKS_URL = f"{settings.CLERK_ISSUER.rstrip('/')}/.well-known/jwks.json"

# Fetch and cache Clerk's public signing keys
jwks_client = PyJWKClient(JWKS_URL)


def verify_clerk_token(token: str) -> dict:
    """
    Verify a Clerk session JWT and return its claims.
    """

    try:
        # Find the public key matching the token's key ID
        signing_key = jwks_client.get_signing_key_from_jwt(token)

        # Verify signature and standard claims
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            issuer=settings.CLERK_ISSUER,
            options={
                "require": ["exp", "iat", "sub"],
            },
        )

        return payload

    except (PyJWTError, PyJWKClientError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )