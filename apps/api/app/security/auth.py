"""Firebase ID token verification + household membership enforcement.

Every protected endpoint calls `get_current_uid` (FastAPI dependency).
Returns 401 on missing/invalid token, 403 when uid is not a household member.
"""
from __future__ import annotations

import os

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

bearer = HTTPBearer(auto_error=False)


def _verify_token(token: str) -> str:
    """Verify a Firebase ID token and return the uid. Raises HTTPException on failure."""
    # In emulator mode accept a bare uid prefixed with "test:" for component tests.
    if os.environ.get("FIRESTORE_EMULATOR_HOST") and token.startswith("test:"):
        return token[len("test:"):]

    try:
        import firebase_admin.auth as fb_auth

        decoded = fb_auth.verify_id_token(token)
        return str(decoded["uid"])
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        ) from exc


async def get_current_uid(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer),
) -> str:
    """FastAPI dependency: verify Bearer token and return the authenticated uid."""
    if creds is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return _verify_token(creds.credentials)


def require_household_member(uid: str, household_id: str) -> None:
    """Raise 403 if uid is not a member of the household (checked via Firestore)."""
    from app.db.firestore import get_db

    db = get_db()
    doc = db.collection("households").document(household_id).get()
    if not doc.exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Household not found")
    members: list[str] = doc.to_dict().get("members", [])
    if uid not in members:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a member of this household",
        )
