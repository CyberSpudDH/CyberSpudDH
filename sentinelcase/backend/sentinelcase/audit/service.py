from sqlalchemy.orm import Session

from sentinelcase.models.core import AuditLog


def log_action(
    db: Session,
    *,
    org_id,
    actor_type: str,
    actor_id: str | None,
    action: str,
    target_type: str | None = None,
    target_id: str | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
    meta: dict | None = None,
):
    db.add(
        AuditLog(
            org_id=org_id,
            actor_type=actor_type,
            actor_id=actor_id,
            action=action,
            target_type=target_type,
            target_id=target_id,
            ip_address=ip_address,
            user_agent=user_agent,
            meta=meta or {},
        )
    )
