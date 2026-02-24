from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from sentinelcase.auth.security import decode_access_token, hash_source_key
from sentinelcase.db import get_db
from sentinelcase.models.core import Source, User

bearer = HTTPBearer(auto_error=False)


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(bearer), db: Session = Depends(get_db)) -> User:
    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    try:
        payload = decode_access_token(credentials.credentials)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from exc
    user = db.get(User, payload.get("sub"))
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User inactive or not found")
    return user


def get_current_source(credentials: HTTPAuthorizationCredentials = Depends(bearer), db: Session = Depends(get_db)) -> Source:
    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Source key required")
    key_hash = hash_source_key(credentials.credentials)
    source = db.scalar(select(Source).where(Source.ingest_api_key_hash == key_hash, Source.enabled.is_(True)))
    if not source:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid source key")
    return source
