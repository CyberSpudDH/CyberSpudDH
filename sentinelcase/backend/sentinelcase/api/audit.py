from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from sentinelcase.db import get_db
from sentinelcase.models.core import AuditLog, User
from sentinelcase.rbac.deps import require_permission

router = APIRouter(prefix="/api/v1/audit", tags=["audit"])


@router.get("")
def list_audit(user: User = Depends(require_permission("audit.read")), db: Session = Depends(get_db)):
    rows = db.scalars(select(AuditLog).where(AuditLog.org_id == user.org_id).order_by(AuditLog.timestamp.desc()).limit(200)).all()
    return [{"action": r.action, "target_type": r.target_type, "target_id": r.target_id, "timestamp": r.timestamp.isoformat()} for r in rows]
