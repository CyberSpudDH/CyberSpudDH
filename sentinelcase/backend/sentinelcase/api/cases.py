from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from sentinelcase.audit.service import log_action
from sentinelcase.ingest.extractor import WEIGHTS
from sentinelcase.db import get_db
from sentinelcase.models.core import Case, CaseObservable, CaseSignal, CaseTimelineEvent, Observation, Signal, Observable, User
from sentinelcase.rbac.deps import require_permission

router = APIRouter(prefix="/api/v1/cases", tags=["cases"])


class CaseIn(BaseModel):
    title: str
    description: str | None = None
    severity: str | None = None
    confidence: int | None = None


class FromSignalIn(BaseModel):
    signal_id: str
    title: str | None = None


class AttachIn(BaseModel):
    signal_id: str


@router.post("")
def create_case(payload: CaseIn, user: User = Depends(require_permission("cases.create")), db: Session = Depends(get_db)):
    count = db.scalar(select(func.count()).select_from(Case).where(Case.org_id == user.org_id)) or 0
    number = f"CASE-{count + 1:06d}"
    case = Case(org_id=user.org_id, case_number=number, title=payload.title, description=payload.description, severity=payload.severity, confidence=payload.confidence, created_by=user.id)
    db.add(case)
    db.flush()
    db.add(CaseTimelineEvent(org_id=user.org_id, case_id=case.id, event_type="case.created", actor_type="user", actor_id=str(user.id), details={"title": case.title}))
    log_action(db, org_id=user.org_id, actor_type="user", actor_id=str(user.id), action="case.create", target_type="case", target_id=str(case.id))
    db.commit()
    return {"id": str(case.id), "case_number": case.case_number}


@router.post(":from-signal")
def create_case_from_signal(payload: FromSignalIn, user: User = Depends(require_permission("cases.create")), db: Session = Depends(get_db)):
    s = db.get(Signal, payload.signal_id)
    if not s or s.org_id != user.org_id:
        raise HTTPException(status_code=404, detail="Signal not found")
    title = payload.title or s.title
    res = create_case(CaseIn(title=title), user, db)
    case_id = res["id"]
    case = db.get(Case, case_id)
    db.add(CaseSignal(org_id=user.org_id, case_id=case.id, signal_id=s.id, attached_by=user.id))
    s.status = "promoted"
    obs_rows = db.scalars(select(Observation).where(Observation.signal_id == s.id)).all()
    for obs in obs_rows:
        existing = db.scalar(select(CaseObservable).where(CaseObservable.case_id == case.id, CaseObservable.observable_id == obs.observable_id))
        if not existing:
            db.add(CaseObservable(org_id=user.org_id, case_id=case.id, observable_id=obs.observable_id, added_by=user.id))
    db.add(CaseTimelineEvent(org_id=user.org_id, case_id=case.id, event_type="signal.attached", actor_type="user", actor_id=str(user.id), details={"signal_id": str(s.id)}))
    log_action(db, org_id=user.org_id, actor_type="user", actor_id=str(user.id), action="case.from_signal", target_type="case", target_id=case_id)
    db.commit()
    return {"id": case_id}


@router.get("")
def list_cases(user: User = Depends(require_permission("cases.read")), db: Session = Depends(get_db)):
    rows = db.scalars(select(Case).where(Case.org_id == user.org_id).order_by(Case.created_at.desc())).all()
    return [{"id": str(c.id), "case_number": c.case_number, "title": c.title, "status": c.status} for c in rows]


@router.get("/{case_id}")
def get_case(case_id: str, user: User = Depends(require_permission("cases.read")), db: Session = Depends(get_db)):
    c = db.get(Case, case_id)
    if not c or c.org_id != user.org_id:
        raise HTTPException(status_code=404, detail="Not found")
    return {"id": str(c.id), "case_number": c.case_number, "title": c.title, "status": c.status}


@router.post("/{case_id}/signals:attach")
def attach_signal(case_id: str, payload: AttachIn, user: User = Depends(require_permission("cases.update")), db: Session = Depends(get_db)):
    c = db.get(Case, case_id)
    s = db.get(Signal, payload.signal_id)
    if not c or not s or c.org_id != user.org_id or s.org_id != user.org_id:
        raise HTTPException(status_code=404, detail="Not found")
    exists = db.scalar(select(CaseSignal).where(CaseSignal.case_id == c.id, CaseSignal.signal_id == s.id))
    if not exists:
        db.add(CaseSignal(org_id=user.org_id, case_id=c.id, signal_id=s.id, attached_by=user.id))
        db.add(CaseTimelineEvent(org_id=user.org_id, case_id=c.id, event_type="signal.attached", actor_type="user", actor_id=str(user.id), details={"signal_id": str(s.id)}))
    db.commit()
    return {"ok": True}


@router.post("/{case_id}/signals:detach")
def detach_signal(case_id: str, payload: AttachIn, user: User = Depends(require_permission("cases.update")), db: Session = Depends(get_db)):
    row = db.scalar(select(CaseSignal).join(Case, Case.id == CaseSignal.case_id).where(CaseSignal.case_id == case_id, CaseSignal.signal_id == payload.signal_id, Case.org_id == user.org_id))
    if not row:
        raise HTTPException(status_code=404, detail="Not found")
    db.delete(row)
    db.add(CaseTimelineEvent(org_id=user.org_id, case_id=case_id, event_type="signal.detached", actor_type="user", actor_id=str(user.id), details={"signal_id": payload.signal_id}))
    db.commit()
    return {"ok": True}


@router.get("/{case_id}/timeline")
def timeline(case_id: str, user: User = Depends(require_permission("cases.read")), db: Session = Depends(get_db)):
    rows = db.scalars(select(CaseTimelineEvent).where(CaseTimelineEvent.org_id == user.org_id, CaseTimelineEvent.case_id == case_id).order_by(CaseTimelineEvent.created_at.asc())).all()
    return [{"event_type": e.event_type, "created_at": e.created_at.isoformat(), "details": e.details} for e in rows]


@router.post("/{case_id}/close")
def close_case(case_id: str, payload: dict, user: User = Depends(require_permission("cases.close")), db: Session = Depends(get_db)):
    c = db.get(Case, case_id)
    if not c or c.org_id != user.org_id:
        raise HTTPException(status_code=404, detail="Not found")
    c.status = "closed"
    c.closed_by = user.id
    c.closed_at = datetime.utcnow()
    c.close_reason = payload.get("reason")
    db.add(CaseTimelineEvent(org_id=user.org_id, case_id=c.id, event_type="case.closed", actor_type="user", actor_id=str(user.id), details={"reason": c.close_reason}))
    db.commit()
    return {"ok": True}


@router.get("/{case_id}/related-signals")
def related_signals(case_id: str, days: int = 30, user: User = Depends(require_permission("cases.read")), db: Session = Depends(get_db)):
    case = db.get(Case, case_id)
    if not case or case.org_id != user.org_id:
        raise HTTPException(status_code=404, detail="Not found")
    case_obs = db.scalars(select(CaseObservable).where(CaseObservable.case_id == case.id, CaseObservable.disposition != "benign")).all()
    observable_ids = [co.observable_id for co in case_obs]
    if not observable_ids:
        return []
    cutoff = datetime.utcnow() - timedelta(days=days)
    obs_rows = db.scalars(select(Observation).where(Observation.org_id == user.org_id, Observation.observable_id.in_(observable_ids), Observation.seen_at >= cutoff)).all()
    score_map: dict[str, dict] = {}
    obs_type_map = {str(o.id): o.type for o in db.scalars(select(Observable).where(Observable.id.in_(observable_ids))).all()}
    for row in obs_rows:
        sig_id = str(row.signal_id)
        current = score_map.setdefault(sig_id, {"signal_id": sig_id, "score": 0, "matches": []})
        obs_type = obs_type_map.get(str(row.observable_id), "ip")
        base = WEIGHTS.get(obs_type, 1)
        age = datetime.utcnow() - row.seen_at
        mult = 1.3 if age <= timedelta(hours=24) else 1.1 if age <= timedelta(days=7) else 1.0
        current["score"] += round(base * mult, 2)
        current["matches"].append({"observable_id": str(row.observable_id), "type": obs_type, "role": row.role})
    return sorted(score_map.values(), key=lambda x: x["score"], reverse=True)
