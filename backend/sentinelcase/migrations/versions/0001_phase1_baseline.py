"""phase1 baseline

Revision ID: 0001_phase1
Revises:
Create Date: 2026-02-20
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001_phase1"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table("orgs", sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True), sa.Column("name", sa.String(255), nullable=False, unique=True), sa.Column("created_at", sa.DateTime(), nullable=False))
    op.create_table("permissions", sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True), sa.Column("key", sa.String(100), nullable=False, unique=True))
    op.create_table("users", sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True), sa.Column("org_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("orgs.id"), nullable=False), sa.Column("email", sa.String(320), nullable=False), sa.Column("display_name", sa.String(255), nullable=False), sa.Column("password_hash", sa.String(255), nullable=False), sa.Column("is_active", sa.Boolean(), nullable=False), sa.Column("created_at", sa.DateTime(), nullable=False), sa.Column("last_login_at", sa.DateTime(), nullable=True), sa.UniqueConstraint("org_id", "email", name="uq_users_org_email"))
    op.create_index("ix_users_org_active", "users", ["org_id", "is_active"])
    op.create_table("roles", sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True), sa.Column("org_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("orgs.id"), nullable=False), sa.Column("name", sa.String(100), nullable=False), sa.Column("description", sa.Text(), nullable=True), sa.Column("is_builtin", sa.Boolean(), nullable=False), sa.Column("created_at", sa.DateTime(), nullable=False), sa.UniqueConstraint("org_id", "name", name="uq_roles_org_name"))
    op.create_table("role_permissions", sa.Column("role_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("roles.id"), primary_key=True), sa.Column("permission_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("permissions.id"), primary_key=True), sa.UniqueConstraint("role_id", "permission_id", name="uq_role_perm"))
    op.create_table("user_roles", sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), primary_key=True), sa.Column("role_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("roles.id"), primary_key=True), sa.UniqueConstraint("user_id", "role_id", name="uq_user_role"))
    op.create_table("sources", sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True), sa.Column("org_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("orgs.id"), nullable=False), sa.Column("name", sa.String(255), nullable=False), sa.Column("description", sa.Text(), nullable=True), sa.Column("ingest_api_key_hash", sa.String(255), nullable=False), sa.Column("enabled", sa.Boolean(), nullable=False), sa.Column("rate_limit_per_min", sa.Integer(), nullable=False), sa.Column("created_at", sa.DateTime(), nullable=False), sa.Column("rotated_at", sa.DateTime(), nullable=True), sa.UniqueConstraint("org_id", "name", name="uq_sources_org_name"))
    op.create_index("ix_sources_org_enabled", "sources", ["org_id", "enabled"])
    op.create_table("signals", sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True), sa.Column("org_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("orgs.id"), nullable=False), sa.Column("source_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("sources.id"), nullable=False), sa.Column("received_at", sa.DateTime(), nullable=False), sa.Column("event_time", sa.DateTime(), nullable=True), sa.Column("title", sa.String(255), nullable=False), sa.Column("raw_payload", postgresql.JSONB(), nullable=False), sa.Column("payload_sha256", sa.String(64), nullable=False), sa.Column("dedupe_key", sa.String(255), nullable=False), sa.Column("status", sa.String(20), nullable=False), sa.Column("triage_disposition", sa.String(50), nullable=True), sa.Column("triaged_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True), sa.Column("triaged_at", sa.DateTime(), nullable=True), sa.UniqueConstraint("org_id", "dedupe_key", name="uq_signals_org_dedupe"))
    op.create_index("ix_signals_org_status_recv", "signals", ["org_id", "status", "received_at"])
    op.create_index("ix_signals_org_source_recv", "signals", ["org_id", "source_id", "received_at"])
    op.create_table("observables", sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True), sa.Column("org_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("orgs.id"), nullable=False), sa.Column("type", sa.String(32), nullable=False), sa.Column("value_normalized", sa.String(1024), nullable=False), sa.Column("first_seen_at", sa.DateTime(), nullable=False), sa.Column("last_seen_at", sa.DateTime(), nullable=False), sa.Column("created_at", sa.DateTime(), nullable=False), sa.UniqueConstraint("org_id", "type", "value_normalized", name="uq_observables_org_type_value"))
    op.create_index("ix_observables_org_type", "observables", ["org_id", "type"])
    op.create_index("ix_observables_org_last_seen", "observables", ["org_id", "last_seen_at"])
    op.create_table("observations", sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True), sa.Column("org_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("orgs.id"), nullable=False), sa.Column("signal_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("signals.id"), nullable=False), sa.Column("observable_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("observables.id"), nullable=False), sa.Column("role", sa.String(64), nullable=True), sa.Column("seen_at", sa.DateTime(), nullable=False), sa.Column("context", postgresql.JSONB(), nullable=False), sa.UniqueConstraint("signal_id", "observable_id", "role", name="uq_obs_signal_observable_role"))
    op.create_index("ix_observations_org_observable_seen", "observations", ["org_id", "observable_id", "seen_at"])
    op.create_index("ix_observations_org_signal", "observations", ["org_id", "signal_id"])
    op.create_table("cases", sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True), sa.Column("org_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("orgs.id"), nullable=False), sa.Column("case_number", sa.String(64), nullable=False), sa.Column("title", sa.String(255), nullable=False), sa.Column("description", sa.Text(), nullable=True), sa.Column("status", sa.String(20), nullable=False), sa.Column("severity", sa.String(20), nullable=True), sa.Column("confidence", sa.Integer(), nullable=True), sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False), sa.Column("created_at", sa.DateTime(), nullable=False), sa.Column("closed_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True), sa.Column("closed_at", sa.DateTime(), nullable=True), sa.Column("close_reason", sa.Text(), nullable=True), sa.UniqueConstraint("org_id", "case_number", name="uq_cases_org_number"))
    op.create_index("ix_cases_org_status_created", "cases", ["org_id", "status", "created_at"])
    op.create_table("case_signals", sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True), sa.Column("org_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("orgs.id"), nullable=False), sa.Column("case_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("cases.id"), nullable=False), sa.Column("signal_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("signals.id"), nullable=False), sa.Column("attached_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False), sa.Column("attached_at", sa.DateTime(), nullable=False), sa.UniqueConstraint("case_id", "signal_id", name="uq_case_signal"))
    op.create_index("ix_case_signals_org_case_attached", "case_signals", ["org_id", "case_id", "attached_at"])
    op.create_index("ix_case_signals_org_signal", "case_signals", ["org_id", "signal_id"])
    op.create_table("case_observables", sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True), sa.Column("org_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("orgs.id"), nullable=False), sa.Column("case_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("cases.id"), nullable=False), sa.Column("observable_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("observables.id"), nullable=False), sa.Column("disposition", sa.String(32), nullable=True), sa.Column("added_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False), sa.Column("added_at", sa.DateTime(), nullable=False), sa.Column("notes", sa.Text(), nullable=True), sa.UniqueConstraint("case_id", "observable_id", name="uq_case_observable"))
    op.create_index("ix_case_observables_org_observable_added", "case_observables", ["org_id", "observable_id", "added_at"])
    op.create_index("ix_case_observables_org_case", "case_observables", ["org_id", "case_id"])
    op.create_table("case_timeline_events", sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True), sa.Column("org_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("orgs.id"), nullable=False), sa.Column("case_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("cases.id"), nullable=False), sa.Column("event_type", sa.String(64), nullable=False), sa.Column("actor_type", sa.String(32), nullable=False), sa.Column("actor_id", sa.String(64), nullable=True), sa.Column("created_at", sa.DateTime(), nullable=False), sa.Column("details", postgresql.JSONB(), nullable=False))
    op.create_index("ix_timeline_org_case_created", "case_timeline_events", ["org_id", "case_id", "created_at"])
    op.create_index("ix_timeline_org_type_created", "case_timeline_events", ["org_id", "event_type", "created_at"])
    op.create_table("audit_logs", sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True), sa.Column("org_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("orgs.id"), nullable=False), sa.Column("actor_type", sa.String(32), nullable=False), sa.Column("actor_id", sa.String(64), nullable=True), sa.Column("action", sa.String(64), nullable=False), sa.Column("target_type", sa.String(64), nullable=True), sa.Column("target_id", sa.String(64), nullable=True), sa.Column("timestamp", sa.DateTime(), nullable=False), sa.Column("ip_address", sa.String(64), nullable=True), sa.Column("user_agent", sa.String(255), nullable=True), sa.Column("meta", postgresql.JSONB(), nullable=False))
    op.create_index("ix_audit_org_timestamp", "audit_logs", ["org_id", "timestamp"])
    op.create_index("ix_audit_org_action_timestamp", "audit_logs", ["org_id", "action", "timestamp"])
    op.create_index("ix_audit_org_target", "audit_logs", ["org_id", "target_type", "target_id"])


def downgrade() -> None:
    for table in ["audit_logs", "case_timeline_events", "case_observables", "case_signals", "cases", "observations", "observables", "signals", "sources", "user_roles", "role_permissions", "roles", "users", "permissions", "orgs"]:
        op.drop_table(table)
