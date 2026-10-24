"""0001_core: Initial core tables and constraints

Revision ID: 0001_core
Revises: 
Create Date: 2026-10-24 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0001_core"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    is_pg = conn.dialect.name == "postgresql"

    # UUID type helper
    uuid_type = postgresql.UUID(as_uuid=True) if is_pg else sa.CHAR(36)
    json_type = postgresql.JSONB if is_pg else sa.JSON()

    # 1. organizations
    op.create_table(
        "organizations",
        sa.Column("id", uuid_type, primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("base_currency", sa.CHAR(3), nullable=False, server_default="USD"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )

    # 2. users
    op.create_table(
        "users",
        sa.Column("id", uuid_type, primary_key=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("display_name", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index("idx_users_email", "users", ["email"])

    # 3. memberships
    op.create_table(
        "memberships",
        sa.Column("id", uuid_type, primary_key=True),
        sa.Column("org_id", uuid_type, sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", uuid_type, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role", sa.String(50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.CheckConstraint("role IN ('owner', 'admin', 'member', 'viewer')", name="check_membership_role"),
        sa.UniqueConstraint("org_id", "user_id", name="uq_memberships_org_user"),
    )
    op.create_index("idx_memberships_org_user", "memberships", ["org_id", "user_id"])

    # 4. audit_logs
    op.create_table(
        "audit_logs",
        sa.Column("id", uuid_type, primary_key=True),
        sa.Column("org_id", uuid_type, sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("actor_user_id", uuid_type, sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("entity_type", sa.String(100), nullable=False),
        sa.Column("entity_id", uuid_type, nullable=True),
        sa.Column("decision", sa.String(50), nullable=True),
        sa.Column("metadata", json_type, nullable=False, server_default=sa.text("'{}'")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index("idx_audit_logs_org_created", "audit_logs", ["org_id", "created_at"])

    # Append-only trigger for audit_logs
    if is_pg:
        op.execute(
            """
            CREATE OR REPLACE FUNCTION prevent_audit_log_mutation()
            RETURNS TRIGGER AS $$
            BEGIN
                RAISE EXCEPTION 'audit_logs table is append-only; update and delete are strictly forbidden';
            END;
            $$ LANGUAGE plpgsql;

            CREATE TRIGGER trg_audit_logs_immutable
            BEFORE UPDATE OR DELETE ON audit_logs
            FOR EACH ROW
            EXECUTE FUNCTION prevent_audit_log_mutation();
            """
        )
    else:
        op.execute(
            """
            CREATE TRIGGER trg_audit_logs_no_update
            BEFORE UPDATE ON audit_logs
            BEGIN
                SELECT RAISE(ABORT, 'audit_logs table is append-only; update is forbidden');
            END;
            """
        )
        op.execute(
            """
            CREATE TRIGGER trg_audit_logs_no_delete
            BEFORE DELETE ON audit_logs
            BEGIN
                SELECT RAISE(ABORT, 'audit_logs table is append-only; delete is forbidden');
            END;
            """
        )

    # 5. decision_runs
    op.create_table(
        "decision_runs",
        sa.Column("id", uuid_type, primary_key=True),
        sa.Column("org_id", uuid_type, sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", uuid_type, sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("kind", sa.String(50), nullable=False),
        sa.Column("status", sa.String(50), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("kind IN ('cfo', 'moonshot', 'chat')", name="check_decision_run_kind"),
        sa.CheckConstraint("status IN ('verified', 'warning', 'unverified', 'failed')", name="check_decision_run_status"),
    )
    op.create_index("idx_decision_runs_org_kind", "decision_runs", ["org_id", "kind"])

    # 6. claims
    op.create_table(
        "claims",
        sa.Column("id", uuid_type, primary_key=True),
        sa.Column("org_id", uuid_type, sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("decision_run_id", uuid_type, sa.ForeignKey("decision_runs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("text", sa.Text, nullable=False),
        sa.Column("tag", sa.String(50), nullable=False),
        sa.Column("status", sa.String(50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.CheckConstraint("tag IN ('cited', 'computed', 'inferred', 'commentary')", name="check_claim_tag"),
        sa.CheckConstraint("status IN ('verified', 'warning', 'unverified', 'failed')", name="check_claim_status"),
    )
    op.create_index("idx_claims_org_decision", "claims", ["org_id", "decision_run_id"])

    # 7. evidence_links
    op.create_table(
        "evidence_links",
        sa.Column("id", uuid_type, primary_key=True),
        sa.Column("org_id", uuid_type, sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("claim_id", uuid_type, sa.ForeignKey("claims.id", ondelete="CASCADE"), nullable=False),
        sa.Column("target_type", sa.String(50), nullable=False),
        sa.Column("target_id", uuid_type, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.CheckConstraint(
            "target_type IN ('source_row', 'financial_record', 'forecast_run', 'forecast_point', "
            "'finance_assumption', 'goal_assumption', 'document_chunk', 'web_source', 'kb_excerpt', "
            "'strategy_score', 'base_rate')",
            name="check_evidence_target_type",
        ),
    )
    op.create_index("idx_evidence_links_org_claim", "evidence_links", ["org_id", "claim_id"])


def downgrade() -> None:
    op.drop_table("evidence_links")
    op.drop_table("claims")
    op.drop_table("decision_runs")
    op.drop_table("audit_logs")
    op.drop_table("memberships")
    op.drop_table("users")
    op.drop_table("organizations")
