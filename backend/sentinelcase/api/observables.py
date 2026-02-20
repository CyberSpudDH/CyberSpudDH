from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from sentinelcase.db import get_db
from sentinelcase.models.core import Observable, Observation, Signal, User
from sentinelcase.rbac.deps import require_permission

router = APIRouter(prefix="/api/v1/observables", tags=["observables"])


@router.get("")
def list_observables(user: User = Depends(require_permission("signals.read")), db: Session = Depends(get_db)):
    rows = db.scalars(select(Observable).where(Observable.org_id == user.org_id).order_by(Observable.last_seen_at.desc())).all()
    return [{"id": str(o.id), "type": o.type, "value_normalized": o.value_normalized, "last_seen_at": o.last_seen_at.isoformat()} for o in rows]


@router.get("/{observable_id}")
def get_observable(observable_id: str, user: User = Depends(require_permission("signals.read")), db: Session = Depends(get_db)):
    o = db.get(Observable, observable_id)
    if not o or o.org_id != user.org_id:
        raise HTTPException(status_code=404, detail="Not found")
    return {"id": str(o.id), "type": o.type, "value_normalized": o.value_normalized}


@router.get("/{observable_id}/signals")
def observable_signals(observable_id: str, user: User = Depends(require_permission("signals.read")), db: Session = Depends(get_db)):
    rows = db.scalars(select(Observation).where(Observation.org_id == user.org_id, Observation.observable_id == observable_id)).all()
    signal_ids = [r.signal_id for r in rows]
    signals = db.scalars(select(Signal).where(Signal.id.in_(signal_ids))).all() if signal_ids else []
    return [{"id": str(s.id), "title": s.title, "status": s.status} for s in signals]
