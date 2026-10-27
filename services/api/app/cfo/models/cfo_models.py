import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.types import CHAR

from services.api.app.core.database import Base
from services.api.app.core.models import UniversalJSON, UniversalUUID


def utc_now():
    return datetime.now(timezone.utc)


class FinanceSettings(Base):
    __tablename__ = "finance_settings"

    id = Column(UniversalUUID, primary_key=True, default=uuid.uuid4)
    org_id = Column(UniversalUUID, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, unique=True)
    reserve_amount = Column(Numeric(18, 2), nullable=False, default=Decimal("50000.00"))
    cash_floor_weeks = Column(Integer, nullable=False, default=12)
    worst_case_delay_days = Column(Integer, nullable=False, default=14)
    worst_case_rev_pct_delta = Column(Numeric(5, 2), nullable=False, default=Decimal("-10.00"))
    best_case_advance_days = Column(Integer, nullable=False, default=7)
    best_case_rev_pct_delta = Column(Numeric(5, 2), nullable=False, default=Decimal("5.00"))
    currency = Column(CHAR(3), nullable=False, default="USD")
    updated_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)

    __table_args__ = (
        Index("idx_finance_settings_org", "org_id"),
    )


class ImportBatch(Base):
    __tablename__ = "import_batches"

    id = Column(UniversalUUID, primary_key=True, default=uuid.uuid4)
    org_id = Column(UniversalUUID, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    filename = Column(String(255), nullable=False)
    content_hash = Column(String(64), nullable=False)
    status = Column(String(50), nullable=False, default="pending")
    total_rows = Column(Integer, nullable=False, default=0)
    accepted_rows = Column(Integer, nullable=False, default=0)
    rejected_rows = Column(Integer, nullable=False, default=0)
    flagged_rows = Column(Integer, nullable=False, default=0)
    column_mapping = Column(UniversalJSON, nullable=False, default=dict)
    quality_report = Column(UniversalJSON, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)

    __table_args__ = (
        CheckConstraint("status IN ('pending', 'needs_mapping', 'processing', 'completed', 'failed')", name="check_import_batch_status"),
        UniqueConstraint("org_id", "content_hash", name="uq_import_batches_org_hash"),
        Index("idx_import_batches_org_created", "org_id", "created_at"),
    )


class SourceRow(Base):
    __tablename__ = "source_rows"

    id = Column(UniversalUUID, primary_key=True, default=uuid.uuid4)
    org_id = Column(UniversalUUID, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    batch_id = Column(UniversalUUID, ForeignKey("import_batches.id", ondelete="CASCADE"), nullable=False)
    row_number = Column(Integer, nullable=False)
    raw_payload = Column(UniversalJSON, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)

    __table_args__ = (
        Index("idx_source_rows_org_batch", "org_id", "batch_id"),
    )


class FinancialRecord(Base):
    __tablename__ = "financial_records"

    id = Column(UniversalUUID, primary_key=True, default=uuid.uuid4)
    org_id = Column(UniversalUUID, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    source_row_id = Column(UniversalUUID, ForeignKey("source_rows.id", ondelete="SET NULL"), nullable=True)
    transaction_date = Column(Date, nullable=False)
    amount = Column(Numeric(18, 2), nullable=False)
    currency = Column(CHAR(3), nullable=False, default="USD")
    category = Column(String(100), nullable=False)
    client_or_vendor = Column(String(255), nullable=True)
    is_actual = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)

    __table_args__ = (
        Index("idx_financial_records_org_date", "org_id", "transaction_date"),
    )


class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(UniversalUUID, primary_key=True, default=uuid.uuid4)
    org_id = Column(UniversalUUID, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    source_row_id = Column(UniversalUUID, ForeignKey("source_rows.id", ondelete="SET NULL"), nullable=True)
    invoice_number = Column(String(100), nullable=False)
    kind = Column(String(20), nullable=False)
    client_or_vendor = Column(String(255), nullable=False)
    amount = Column(Numeric(18, 2), nullable=False)
    currency = Column(CHAR(3), nullable=False, default="USD")
    issue_date = Column(Date, nullable=False)
    due_date = Column(Date, nullable=False)
    expected_payment_date = Column(Date, nullable=False)
    status = Column(String(50), nullable=False, default="issued")
    is_uncertain = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)

    __table_args__ = (
        CheckConstraint("kind IN ('receivable', 'payable')", name="check_invoice_kind"),
        CheckConstraint("status IN ('draft', 'issued', 'paid', 'late', 'disputed', 'written_off')", name="check_invoice_status"),
        UniqueConstraint("org_id", "invoice_number", name="uq_invoices_org_number"),
        Index("idx_invoices_org_expected", "org_id", "expected_payment_date"),
    )


class PayrollItem(Base):
    __tablename__ = "payroll_items"

    id = Column(UniversalUUID, primary_key=True, default=uuid.uuid4)
    org_id = Column(UniversalUUID, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    source_row_id = Column(UniversalUUID, ForeignKey("source_rows.id", ondelete="SET NULL"), nullable=True)
    employee_identifier = Column(String(100), nullable=False)
    role_title = Column(String(255), nullable=False)
    monthly_gross = Column(Numeric(18, 2), nullable=False)
    benefits_and_taxes = Column(Numeric(18, 2), nullable=False, default=Decimal("0.00"))
    currency = Column(CHAR(3), nullable=False, default="USD")
    pay_frequency = Column(String(50), nullable=False, default="monthly")
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)

    __table_args__ = (
        CheckConstraint("pay_frequency IN ('weekly', 'biweekly', 'monthly')", name="check_payroll_frequency"),
        Index("idx_payroll_items_org", "org_id"),
    )


class FinanceAssumption(Base):
    __tablename__ = "finance_assumptions"

    id = Column(UniversalUUID, primary_key=True, default=uuid.uuid4)
    org_id = Column(UniversalUUID, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    category = Column(String(100), nullable=False)
    key = Column(String(100), nullable=False)
    value = Column(UniversalJSON, nullable=False)
    valid_from = Column(Date, nullable=False)
    valid_to = Column(Date, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)

    __table_args__ = (
        Index("idx_finance_assumptions_org_key", "org_id", "key"),
    )


class Scenario(Base):
    __tablename__ = "scenarios"

    id = Column(UniversalUUID, primary_key=True, default=uuid.uuid4)
    org_id = Column(UniversalUUID, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    baseline_run_id = Column(UniversalUUID, nullable=False)
    name = Column(String(255), nullable=False)
    origin = Column(String(50), nullable=False, default="user")
    source_card_id = Column(UniversalUUID, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)

    __table_args__ = (
        CheckConstraint("origin IN ('user', 'moonshot_card')", name="check_scenario_origin"),
        Index("idx_scenarios_org", "org_id"),
    )


class ScenarioChange(Base):
    __tablename__ = "scenario_changes"

    id = Column(UniversalUUID, primary_key=True, default=uuid.uuid4)
    org_id = Column(UniversalUUID, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    scenario_id = Column(UniversalUUID, ForeignKey("scenarios.id", ondelete="CASCADE"), nullable=False)
    lever = Column(String(100), nullable=False)
    op = Column(String(20), nullable=False, default="set")
    value = Column(String(100), nullable=False)
    start_date = Column(Date, nullable=True)
    params = Column(UniversalJSON, nullable=False, default=dict)
    is_assumption = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)

    __table_args__ = (
        CheckConstraint("op IN ('set', 'add', 'multiply')", name="check_scenario_change_op"),
        Index("idx_scenario_changes_org_scen", "org_id", "scenario_id"),
    )


class ForecastRun(Base):
    __tablename__ = "forecast_runs"

    id = Column(UniversalUUID, primary_key=True, default=uuid.uuid4)
    org_id = Column(UniversalUUID, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    scenario_id = Column(UniversalUUID, ForeignKey("scenarios.id", ondelete="CASCADE"), nullable=True)
    case_type = Column(String(20), nullable=False, default="baseline")
    engine_version = Column(String(50), nullable=False, default="0.1.0")
    horizon_weeks = Column(Integer, nullable=False, default=26)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    min_cash = Column(Numeric(18, 2), nullable=False)
    min_cash_date = Column(Date, nullable=False)
    end_cash = Column(Numeric(18, 2), nullable=False)
    runway_weeks = Column(Integer, nullable=True)
    reserve_breach = Column(Boolean, nullable=False, default=False)
    cash_floor_breach = Column(Boolean, nullable=False, default=False)
    status = Column(String(50), nullable=False, default="verified")
    baseline_hash = Column(String(64), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)

    __table_args__ = (
        CheckConstraint("case_type IN ('baseline', 'expected', 'best', 'worst')", name="check_forecast_case_type"),
        CheckConstraint("status IN ('verified', 'warning', 'unverified', 'failed')", name="check_forecast_run_status"),
        Index("idx_forecast_runs_org_created", "org_id", "created_at"),
    )


class ForecastPoint(Base):
    __tablename__ = "forecast_points"

    id = Column(UniversalUUID, primary_key=True, default=uuid.uuid4)
    org_id = Column(UniversalUUID, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    run_id = Column(UniversalUUID, ForeignKey("forecast_runs.id", ondelete="CASCADE"), nullable=False)
    week_number = Column(Integer, nullable=False)
    week_start = Column(Date, nullable=False)
    opening_cash = Column(Numeric(18, 2), nullable=False)
    projected_inflows = Column(Numeric(18, 2), nullable=False)
    projected_outflows = Column(Numeric(18, 2), nullable=False)
    net_cash_flow = Column(Numeric(18, 2), nullable=False)
    closing_cash = Column(Numeric(18, 2), nullable=False)
    value_label = Column(String(50), nullable=False, default="calculated")
    contributing_inflow_refs = Column(UniversalJSON, nullable=False, default=list)
    contributing_outflow_refs = Column(UniversalJSON, nullable=False, default=list)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)

    __table_args__ = (
        CheckConstraint("value_label IN ('observed', 'calculated', 'estimated', 'hypothetical')", name="check_forecast_point_label"),
        Index("idx_forecast_points_run_week", "run_id", "week_number"),
    )


class AnomalyFlag(Base):
    __tablename__ = "anomaly_flags"

    id = Column(UniversalUUID, primary_key=True, default=uuid.uuid4)
    org_id = Column(UniversalUUID, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    source_row_id = Column(UniversalUUID, ForeignKey("source_rows.id", ondelete="SET NULL"), nullable=True)
    entity_type = Column(String(100), nullable=False)
    entity_id = Column(UniversalUUID, nullable=True)
    anomaly_type = Column(String(100), nullable=False)
    severity = Column(String(50), nullable=False, default="warning")
    details = Column(UniversalJSON, nullable=False, default=dict)
    status = Column(String(50), nullable=False, default="flagged")
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)

    __table_args__ = (
        CheckConstraint("severity IN ('info', 'warning', 'critical')", name="check_anomaly_severity"),
        CheckConstraint("status IN ('flagged', 'reviewed', 'resolved', 'ignored')", name="check_anomaly_status"),
        Index("idx_anomaly_flags_org_status", "org_id", "status"),
    )
