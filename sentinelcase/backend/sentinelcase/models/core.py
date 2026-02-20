import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from sentinelcase.db import Base


class Org(Base):
    __tablename__ = "orgs"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class User(Base):
    __tablename__ = "users"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("orgs.id"), index=True)
    email: Mapped[str] = mapped_column(String(320))
    display_name: Mapped[str] = mapped_column(String(255))
    password_hash: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    __table_args__ = (UniqueConstraint("org_id", "email", name="uq_users_org_email"), Index("ix_users_org_active", "org_id", "is_active"))


class Role(Base):
    __tablename__ = "roles"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("orgs.id"), index=True)
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_builtin: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    __table_args__ = (UniqueConstraint("org_id", "name", name="uq_roles_org_name"),)


class Permission(Base):
    __tablename__ = "permissions"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    key: Mapped[str] = mapped_column(String(100), unique=True)


class RolePermission(Base):
    __tablename__ = "role_permissions"
    role_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("roles.id"), primary_key=True)
    permission_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("permissions.id"), primary_key=True)
    __table_args__ = (UniqueConstraint("role_id", "permission_id", name="uq_role_perm"),)


class UserRole(Base):
    __tablename__ = "user_roles"
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True)
    role_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("roles.id"), primary_key=True)
    __table_args__ = (UniqueConstraint("user_id", "role_id", name="uq_user_role"),)


class Source(Base):
    __tablename__ = "sources"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("orgs.id"), index=True)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    ingest_api_key_hash: Mapped[str] = mapped_column(String(255))
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    rate_limit_per_min: Mapped[int] = mapped_column(Integer, default=60)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    rotated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    __table_args__ = (UniqueConstraint("org_id", "name", name="uq_sources_org_name"), Index("ix_sources_org_enabled", "org_id", "enabled"))


class Signal(Base):
    __tablename__ = "signals"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("orgs.id"), index=True)
    source_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("sources.id"), index=True)
    received_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    event_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    title: Mapped[str] = mapped_column(String(255), default="Signal")
    raw_payload: Mapped[dict] = mapped_column(JSONB)
    payload_sha256: Mapped[str] = mapped_column(String(64))
    dedupe_key: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(20), default="new")
    triage_disposition: Mapped[str | None] = mapped_column(String(50), nullable=True)
    triaged_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    triaged_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    __table_args__ = (
        UniqueConstraint("org_id", "dedupe_key", name="uq_signals_org_dedupe"),
        Index("ix_signals_org_status_recv", "org_id", "status", "received_at"),
        Index("ix_signals_org_source_recv", "org_id", "source_id", "received_at"),
    )


class Observable(Base):
    __tablename__ = "observables"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("orgs.id"), index=True)
    type: Mapped[str] = mapped_column(String(32))
    value_normalized: Mapped[str] = mapped_column(String(1024))
    first_seen_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    __table_args__ = (
        UniqueConstraint("org_id", "type", "value_normalized", name="uq_observables_org_type_value"),
        Index("ix_observables_org_type", "org_id", "type"),
        Index("ix_observables_org_last_seen", "org_id", "last_seen_at"),
    )


class Observation(Base):
    __tablename__ = "observations"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("orgs.id"), index=True)
    signal_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("signals.id"), index=True)
    observable_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("observables.id"), index=True)
    role: Mapped[str | None] = mapped_column(String(64), nullable=True)
    seen_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    context: Mapped[dict] = mapped_column(JSONB, default=dict)
    __table_args__ = (
        UniqueConstraint("signal_id", "observable_id", "role", name="uq_obs_signal_observable_role"),
        Index("ix_observations_org_observable_seen", "org_id", "observable_id", "seen_at"),
        Index("ix_observations_org_signal", "org_id", "signal_id"),
    )


class Case(Base):
    __tablename__ = "cases"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("orgs.id"), index=True)
    case_number: Mapped[str] = mapped_column(String(64))
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="open")
    severity: Mapped[str | None] = mapped_column(String(20), nullable=True)
    confidence: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    closed_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    close_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    __table_args__ = (UniqueConstraint("org_id", "case_number", name="uq_cases_org_number"), Index("ix_cases_org_status_created", "org_id", "status", "created_at"))


class CaseSignal(Base):
    __tablename__ = "case_signals"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("orgs.id"), index=True)
    case_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("cases.id"), index=True)
    signal_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("signals.id"), index=True)
    attached_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    attached_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    __table_args__ = (
        UniqueConstraint("case_id", "signal_id", name="uq_case_signal"),
        Index("ix_case_signals_org_case_attached", "org_id", "case_id", "attached_at"),
        Index("ix_case_signals_org_signal", "org_id", "signal_id"),
    )


class CaseObservable(Base):
    __tablename__ = "case_observables"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("orgs.id"), index=True)
    case_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("cases.id"), index=True)
    observable_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("observables.id"), index=True)
    disposition: Mapped[str | None] = mapped_column(String(32), nullable=True)
    added_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    added_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    __table_args__ = (
        UniqueConstraint("case_id", "observable_id", name="uq_case_observable"),
        Index("ix_case_observables_org_observable_added", "org_id", "observable_id", "added_at"),
        Index("ix_case_observables_org_case", "org_id", "case_id"),
    )


class CaseTimelineEvent(Base):
    __tablename__ = "case_timeline_events"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("orgs.id"), index=True)
    case_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("cases.id"), index=True)
    event_type: Mapped[str] = mapped_column(String(64), index=True)
    actor_type: Mapped[str] = mapped_column(String(32))
    actor_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    details: Mapped[dict] = mapped_column(JSONB, default=dict)
    __table_args__ = (Index("ix_timeline_org_case_created", "org_id", "case_id", "created_at"), Index("ix_timeline_org_type_created", "org_id", "event_type", "created_at"))


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("orgs.id"), index=True)
    actor_type: Mapped[str] = mapped_column(String(32))
    actor_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    action: Mapped[str] = mapped_column(String(64), index=True)
    target_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    target_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(255), nullable=True)
    meta: Mapped[dict] = mapped_column(JSONB, default=dict)
    __table_args__ = (
        Index("ix_audit_org_timestamp", "org_id", "timestamp"),
        Index("ix_audit_org_action_timestamp", "org_id", "action", "timestamp"),
        Index("ix_audit_org_target", "org_id", "target_type", "target_id"),
    )
