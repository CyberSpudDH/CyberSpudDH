from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from sentinelcase.audit.service import log_action
from sentinelcase.auth.deps import get_current_user
from sentinelcase.auth.security import generate_source_key, hash_source_key
from sentinelcase.db import get_db
from sentinelcase.models.core import Source, User
from sentinelcase.rbac.deps import require_permission

router = APIRouter(prefix="/api/v1/sources", tags=["sources"])


class SourceIn(BaseModel):
    name: str
    description: str | None = None
    rate_limit_per_min: int = 60


class SourcePatch(BaseModel):
    description: str | None = None
    enabled: bool | None = None
    rate_limit_per_min: int | None = None


@router.post("")
def create_source(payload: SourceIn, user: User = Depends(require_permission("sources.manage")), db: Session = Depends(get_db)):
    exists = db.scalar(select(Source).where(Source.org_id == user.org_id, Source.name == payload.name))
    if exists:
        raise HTTPException(status_code=409, detail="Source exists")
    raw_key = generate_source_key()
    source = Source(org_id=user.org_id, name=payload.name, description=payload.description, ingest_api_key_hash=hash_source_key(raw_key), rate_limit_per_min=payload.rate_limit_per_min)
    db.add(source)
    log_action(db, org_id=user.org_id, actor_type="user", actor_id=str(user.id), action="source.create", target_type="source", target_id=str(source.id), meta={"name": payload.name})
    db.commit()
    db.refresh(source)
    return {"id": str(source.id), "name": source.name, "api_key": raw_key}


@router.get("")
def list_sources(user: User = Depends(require_permission("sources.manage")), db: Session = Depends(get_db)):
    rows = db.scalars(select(Source).where(Source.org_id == user.org_id).order_by(Source.created_at.desc())).all()
    return [{"id": str(s.id), "name": s.name, "enabled": s.enabled, "rate_limit_per_min": s.rate_limit_per_min} for s in rows]


@router.patch("/{source_id}")
def patch_source(source_id: str, payload: SourcePatch, user: User = Depends(require_permission("sources.manage")), db: Session = Depends(get_db)):
    source = db.get(Source, source_id)
    if not source or source.org_id != user.org_id:
        raise HTTPException(status_code=404, detail="Not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(source, k, v)
    log_action(db, org_id=user.org_id, actor_type="user", actor_id=str(user.id), action="source.update", target_type="source", target_id=source_id)
    db.commit()
    return {"ok": True}


@router.post("/{source_id}/rotate-key")
def rotate_source_key(source_id: str, user: User = Depends(require_permission("sources.manage")), db: Session = Depends(get_db)):
    source = db.get(Source, source_id)
    if not source or source.org_id != user.org_id:
        raise HTTPException(status_code=404, detail="Not found")
    raw = generate_source_key()
    source.ingest_api_key_hash = hash_source_key(raw)
    source.rotated_at = datetime.utcnow()
    log_action(db, org_id=user.org_id, actor_type="user", actor_id=str(user.id), action="source.rotate_key", target_type="source", target_id=source_id)
    db.commit()
    return {"api_key": raw}
