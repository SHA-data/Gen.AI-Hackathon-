import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.types import JSON, TypeDecorator, CHAR
from services.api.app.core.database import Base


# Universal UUID column type compatible with PostgreSQL and SQLite
class UniversalUUID(TypeDecorator):
    impl = CHAR(36)
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PG_UUID(as_uuid=True))
        else:
            return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if isinstance(value, uuid.UUID):
            return str(value) if dialect.name != "postgresql" else value
        return str(uuid.UUID(str(value))) if dialect.name != "postgresql" else uuid.UUID(str(value))

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        if isinstance(value, uuid.UUID):
            return value
        return uuid.UUID(str(value))


# Universal JSON column type compatible with PostgreSQL JSONB and SQLite JSON
class UniversalJSON(TypeDecorator):
    impl = JSON
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(JSONB)
        else:
            return dialect.type_descriptor(JSON)


def utc_now():
    return datetime.now(timezone.utc)


class Organization(Base):
    __tablename__ = "organizations"

    id = Column(UniversalUUID, primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    base_currency = Column(CHAR(3), nullable=False, default="USD")
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)


class User(Base):
    __tablename__ = "users"

    id = Column(UniversalUUID, primary_key=True, default=uuid.uuid4)
    email = Column(String(255), nullable=False, unique=True, index=True)
    display_name = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)


class Membership(Base):
    __tablename__ = "memberships"

    id = Column(UniversalUUID, primary_key=True, default=uuid.uuid4)
    org_id = Column(UniversalUUID, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UniversalUUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(50), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)

    __table_args__ = (
        CheckConstraint("role IN ('owner', 'admin', 'member', 'viewer')", name="check_membership_role"),
        UniqueConstraint("org_id", "user_id", name="uq_memberships_org_user"),
        Index("idx_memberships_org_user", "org_id", "user_id"),
    )


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(UniversalUUID, primary_key=True, default=uuid.uuid4)
    org_id = Column(UniversalUUID, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    actor_user_id = Column(UniversalUUID, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    action = Column(String(100), nullable=False)
    entity_type = Column(String(100), nullable=False)
    entity_id = Column(UniversalUUID, nullable=True)
    decision = Column(String(50), nullable=True)
    extra_metadata = Column("metadata", UniversalJSON, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)

    __table_args__ = (
        Index("idx_audit_logs_org_created", "org_id", "created_at"),
    )


class DecisionRun(Base):
    __tablename__ = "decision_runs"

    id = Column(UniversalUUID, primary_key=True, default=uuid.uuid4)
    org_id = Column(UniversalUUID, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UniversalUUID, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    kind = Column(String(50), nullable=False)
    status = Column(String(50), nullable=False)
    started_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)
    finished_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        CheckConstraint("kind IN ('cfo', 'moonshot', 'chat')", name="check_decision_run_kind"),
        CheckConstraint("status IN ('verified', 'warning', 'unverified', 'failed')", name="check_decision_run_status"),
        Index("idx_decision_runs_org_kind", "org_id", "kind"),
    )


class Claim(Base):
    __tablename__ = "claims"

    id = Column(UniversalUUID, primary_key=True, default=uuid.uuid4)
    org_id = Column(UniversalUUID, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    decision_run_id = Column(UniversalUUID, ForeignKey("decision_runs.id", ondelete="CASCADE"), nullable=False)
    text = Column(Text, nullable=False)
    tag = Column(String(50), nullable=False)
    status = Column(String(50), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)

    __table_args__ = (
        CheckConstraint("tag IN ('cited', 'computed', 'inferred', 'commentary')", name="check_claim_tag"),
        CheckConstraint("status IN ('verified', 'warning', 'unverified', 'failed')", name="check_claim_status"),
        Index("idx_claims_org_decision", "org_id", "decision_run_id"),
    )


class EvidenceLink(Base):
    __tablename__ = "evidence_links"

    id = Column(UniversalUUID, primary_key=True, default=uuid.uuid4)
    org_id = Column(UniversalUUID, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    claim_id = Column(UniversalUUID, ForeignKey("claims.id", ondelete="CASCADE"), nullable=False)
    target_type = Column(String(50), nullable=False)
    target_id = Column(UniversalUUID, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)

    __table_args__ = (
        CheckConstraint(
            "target_type IN ('source_row', 'financial_record', 'forecast_run', 'forecast_point', "
            "'finance_assumption', 'goal_assumption', 'document_chunk', 'web_source', 'kb_excerpt', "
            "'strategy_score', 'base_rate')",
            name="check_evidence_target_type",
        ),
        Index("idx_evidence_links_org_claim", "org_id", "claim_id"),
    )
