import hashlib
from datetime import datetime

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from sentinelcase.audit.service import log_action
from sentinelcase.auth.deps import get_current_source
from sentinelcase.db import get_db
from sentinelcase.ingest.extractor import extract_observables
from sentinelcase.models.core import Observable, Observation, Signal, Source
from sentinelcase.auth.deps import get_current_user
from sentinelcase.models.core import User
from sentinelcase.rbac.deps import require_permission

router = APIRouter(prefix="/api/v1/signals", tags=["signals"])


@router.post(":ingest")
def ingest_signal(payload: dict, idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"), source: Source = Depends(get_current_source), db: Session = Depends(get_db)):
    dedupe_key = idempotency_key or hashlib.sha256(str(payload).encode()).hexdigest()
    existing = db.scalar(select(Signal).where(Signal.org_id == source.org_id, Signal.dedupe_key == dedupe_key))
    if existing:
        return {"id": str(existing.id), "deduped": True}

    payload_sha = hashlib.sha256(str(payload).encode()).hexdigest()
    signal = Signal(org_id=source.org_id, source_id=source.id, raw_payload=payload, payload_sha256=payload_sha, dedupe_key=dedupe_key, title=payload.get("title", "Signal"))
    db.add(signal)
    db.flush()

    extracted = extract_observables(payload)
    for obs in extracted:
        o = db.scalar(select(Observable).where(Observable.org_id == source.org_id, Observable.type == obs["type"], Observable.value_normalized == obs["value"]))
        if not o:
            o = Observable(org_id=source.org_id, type=obs["type"], value_normalized=obs["value"]) 
            db.add(o)
            db.flush()
        o.last_seen_at = datetime.utcnow()
        link = db.scalar(select(Observation).where(Observation.signal_id == signal.id, Observation.observable_id == o.id, Observation.role == obs.get("role")))
        if not link:
            db.add(Observation(org_id=source.org_id, signal_id=signal.id, observable_id=o.id, role=obs.get("role"), context=obs.get("context", {})))

    log_action(db, org_id=source.org_id, actor_type="source", actor_id=str(source.id), action="signal.ingest", target_type="signal", target_id=str(signal.id))
    db.commit()
    return {"id": str(signal.id), "deduped": False}


@router.get("")
def list_signals(user: User = Depends(require_permission("signals.read")), db: Session = Depends(get_db)):
    rows = db.scalars(select(Signal).where(Signal.org_id == user.org_id).order_by(Signal.received_at.desc())).all()
    return [{"id": str(r.id), "status": r.status, "title": r.title, "received_at": r.received_at.isoformat()} for r in rows]


@router.get("/{signal_id}")
def get_signal(signal_id: str, user: User = Depends(require_permission("signals.read")), db: Session = Depends(get_db)):
    s = db.get(Signal, signal_id)
    if not s or s.org_id != user.org_id:
        raise HTTPException(status_code=404, detail="Not found")
    return {"id": str(s.id), "status": s.status, "payload": s.raw_payload}


@router.post("/{signal_id}/hold")
def hold_signal(signal_id: str, user: User = Depends(require_permission("signals.triage")), db: Session = Depends(get_db)):
    s = db.get(Signal, signal_id)
    if not s or s.org_id != user.org_id:
        raise HTTPException(status_code=404, detail="Not found")
    s.status = "held"
    s.triage_disposition = "held"
    s.triaged_by = user.id
    s.triaged_at = datetime.utcnow()
    log_action(db, org_id=user.org_id, actor_type="user", actor_id=str(user.id), action="signal.hold", target_type="signal", target_id=signal_id)
    db.commit()
    return {"ok": True}


@router.post("/{signal_id}/dismiss")
def dismiss_signal(signal_id: str, user: User = Depends(require_permission("signals.dismiss")), db: Session = Depends(get_db)):
    s = db.get(Signal, signal_id)
    if not s or s.org_id != user.org_id:
        raise HTTPException(status_code=404, detail="Not found")
    s.status = "dismissed"
    s.triage_disposition = "dismissed"
    s.triaged_by = user.id
    s.triaged_at = datetime.utcnow()
    log_action(db, org_id=user.org_id, actor_type="user", actor_id=str(user.id), action="signal.dismiss", target_type="signal", target_id=signal_id)
    db.commit()
    return {"ok": True}
