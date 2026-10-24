"""0100_cfo_tables: The 12 NeuralCFO tables, indexes, and constraints

Revision ID: 0100_cfo_tables
Revises: 0001_core
Create Date: 2026-10-24 12:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0100_cfo_tables"
down_revision: Union[str, None] = "0001_core"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    is_pg = conn.dialect.name == "postgresql"

    uuid_type = postgresql.UUID(as_uuid=True) if is_pg else sa.CHAR(36)
    json_type = postgresql.JSONB if is_pg else sa.JSON()

    # 1. finance_settings
    op.create_table(
        "finance_settings",
        sa.Column("id", uuid_type, primary_key=True),
        sa.Column("org_id", uuid_type, sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("reserve_amount", sa.Numeric(18, 2), nullable=False, server_default="50000.00"),
        sa.Column("cash_floor_weeks", sa.Integer(), nullable=False, server_default="12"),
        sa.Column("worst_case_delay_days", sa.Integer(), nullable=False, server_default="14"),
        sa.Column("worst_case_rev_pct_delta", sa.Numeric(5, 2), nullable=False, server_default="-10.00"),
        sa.Column("best_case_advance_days", sa.Integer(), nullable=False, server_default="7"),
        sa.Column("best_case_rev_pct_delta", sa.Numeric(5, 2), nullable=False, server_default="5.00"),
        sa.Column("currency", sa.CHAR(3), nullable=False, server_default="USD"),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index("idx_finance_settings_org", "finance_settings", ["org_id"])

    # 2. import_batches
    op.create_table(
        "import_batches",
        sa.Column("id", uuid_type, primary_key=True),
        sa.Column("org_id", uuid_type, sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("filename", sa.String(255), nullable=False),
        sa.Column("content_hash", sa.String(64), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, server_default="pending"),
        sa.Column("total_rows", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("accepted_rows", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("rejected_rows", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("flagged_rows", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("column_mapping", json_type, nullable=False, server_default=sa.text("'{}'")),
        sa.Column("quality_report", json_type, nullable=False, server_default=sa.text("'{}'")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.CheckConstraint("status IN ('pending', 'needs_mapping', 'processing', 'completed', 'failed')", name="check_import_batch_status"),
        sa.UniqueConstraint("org_id", "content_hash", name="uq_import_batches_org_hash"),
    )
    op.create_index("idx_import_batches_org_created", "import_batches", ["org_id", "created_at"])

    # 3. source_rows
    op.create_table(
        "source_rows",
        sa.Column("id", uuid_type, primary_key=True),
        sa.Column("org_id", uuid_type, sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("batch_id", uuid_type, sa.ForeignKey("import_batches.id", ondelete="CASCADE"), nullable=False),
        sa.Column("row_number", sa.Integer(), nullable=False),
        sa.Column("raw_payload", json_type, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index("idx_source_rows_org_batch", "source_rows", ["org_id", "batch_id"])

    # 4. financial_records
    op.create_table(
        "financial_records",
        sa.Column("id", uuid_type, primary_key=True),
        sa.Column("org_id", uuid_type, sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("source_row_id", uuid_type, sa.ForeignKey("source_rows.id", ondelete="SET NULL"), nullable=True),
        sa.Column("transaction_date", sa.Date(), nullable=False),
        sa.Column("amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("currency", sa.CHAR(3), nullable=False, server_default="USD"),
        sa.Column("category", sa.String(100), nullable=False),
        sa.Column("client_or_vendor", sa.String(255), nullable=True),
        sa.Column("is_actual", sa.Boolean(), nullable=False, server_default=sa.text("1" if not is_pg else "true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index("idx_financial_records_org_date", "financial_records", ["org_id", "transaction_date"])

    # 5. invoices
    op.create_table(
        "invoices",
        sa.Column("id", uuid_type, primary_key=True),
        sa.Column("org_id", uuid_type, sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("source_row_id", uuid_type, sa.ForeignKey("source_rows.id", ondelete="SET NULL"), nullable=True),
        sa.Column("invoice_number", sa.String(100), nullable=False),
        sa.Column("kind", sa.String(20), nullable=False),
        sa.Column("client_or_vendor", sa.String(255), nullable=False),
        sa.Column("amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("currency", sa.CHAR(3), nullable=False, server_default="USD"),
        sa.Column("issue_date", sa.Date(), nullable=False),
        sa.Column("due_date", sa.Date(), nullable=False),
        sa.Column("expected_payment_date", sa.Date(), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, server_default="issued"),
        sa.Column("is_uncertain", sa.Boolean(), nullable=False, server_default=sa.text("0" if not is_pg else "false")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.CheckConstraint("kind IN ('receivable', 'payable')", name="check_invoice_kind"),
        sa.CheckConstraint("status IN ('draft', 'issued', 'paid', 'late', 'disputed', 'written_off')", name="check_invoice_status"),
        sa.UniqueConstraint("org_id", "invoice_number", name="uq_invoices_org_number"),
    )
    op.create_index("idx_invoices_org_expected", "invoices", ["org_id", "expected_payment_date"])

    # 6. payroll_items
    op.create_table(
        "payroll_items",
        sa.Column("id", uuid_type, primary_key=True),
        sa.Column("org_id", uuid_type, sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("source_row_id", uuid_type, sa.ForeignKey("source_rows.id", ondelete="SET NULL"), nullable=True),
        sa.Column("employee_identifier", sa.String(100), nullable=False),
        sa.Column("role_title", sa.String(255), nullable=False),
        sa.Column("monthly_gross", sa.Numeric(18, 2), nullable=False),
        sa.Column("benefits_and_taxes", sa.Numeric(18, 2), nullable=False, server_default="0.00"),
        sa.Column("currency", sa.CHAR(3), nullable=False, server_default="USD"),
        sa.Column("pay_frequency", sa.String(50), nullable=False, server_default="monthly"),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.CheckConstraint("pay_frequency IN ('weekly', 'biweekly', 'monthly')", name="check_payroll_frequency"),
    )
    op.create_index("idx_payroll_items_org", "payroll_items", ["org_id"])

    # 7. finance_assumptions
    op.create_table(
        "finance_assumptions",
        sa.Column("id", uuid_type, primary_key=True),
        sa.Column("org_id", uuid_type, sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("category", sa.String(100), nullable=False),
        sa.Column("key", sa.String(100), nullable=False),
        sa.Column("value", json_type, nullable=False),
        sa.Column("valid_from", sa.Date(), nullable=False),
        sa.Column("valid_to", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index("idx_finance_assumptions_org_key", "finance_assumptions", ["org_id", "key"])

    # 8. scenarios
    op.create_table(
        "scenarios",
        sa.Column("id", uuid_type, primary_key=True),
        sa.Column("org_id", uuid_type, sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("baseline_run_id", uuid_type, nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("origin", sa.String(50), nullable=False, server_default="user"),
        sa.Column("source_card_id", uuid_type, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.CheckConstraint("origin IN ('user', 'moonshot_card')", name="check_scenario_origin"),
    )
    op.create_index("idx_scenarios_org", "scenarios", ["org_id"])

    # 9. scenario_changes
    op.create_table(
        "scenario_changes",
        sa.Column("id", uuid_type, primary_key=True),
        sa.Column("org_id", uuid_type, sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("scenario_id", uuid_type, sa.ForeignKey("scenarios.id", ondelete="CASCADE"), nullable=False),
        sa.Column("lever", sa.String(100), nullable=False),
        sa.Column("op", sa.String(20), nullable=False, server_default="set"),
        sa.Column("value", sa.String(100), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("params", json_type, nullable=False, server_default=sa.text("'{}'")),
        sa.Column("is_assumption", sa.Boolean(), nullable=False, server_default=sa.text("1" if not is_pg else "true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.CheckConstraint("op IN ('set', 'add', 'multiply')", name="check_scenario_change_op"),
    )
    op.create_index("idx_scenario_changes_org_scen", "scenario_changes", ["org_id", "scenario_id"])

    # 10. forecast_runs
    op.create_table(
        "forecast_runs",
        sa.Column("id", uuid_type, primary_key=True),
        sa.Column("org_id", uuid_type, sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("scenario_id", uuid_type, sa.ForeignKey("scenarios.id", ondelete="CASCADE"), nullable=True),
        sa.Column("case_type", sa.String(20), nullable=False, server_default="baseline"),
        sa.Column("engine_version", sa.String(50), nullable=False, server_default="0.1.0"),
        sa.Column("horizon_weeks", sa.Integer(), nullable=False, server_default="26"),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("min_cash", sa.Numeric(18, 2), nullable=False),
        sa.Column("min_cash_date", sa.Date(), nullable=False),
        sa.Column("end_cash", sa.Numeric(18, 2), nullable=False),
        sa.Column("runway_weeks", sa.Integer(), nullable=True),
        sa.Column("reserve_breach", sa.Boolean(), nullable=False, server_default=sa.text("0" if not is_pg else "false")),
        sa.Column("cash_floor_breach", sa.Boolean(), nullable=False, server_default=sa.text("0" if not is_pg else "false")),
        sa.Column("status", sa.String(50), nullable=False, server_default="verified"),
        sa.Column("baseline_hash", sa.String(64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.CheckConstraint("case_type IN ('baseline', 'expected', 'best', 'worst')", name="check_forecast_case_type"),
        sa.CheckConstraint("status IN ('verified', 'warning', 'unverified', 'failed')", name="check_forecast_run_status"),
    )
    op.create_index("idx_forecast_runs_org_created", "forecast_runs", ["org_id", "created_at"])

    # 11. forecast_points
    op.create_table(
        "forecast_points",
        sa.Column("id", uuid_type, primary_key=True),
        sa.Column("org_id", uuid_type, sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("run_id", uuid_type, sa.ForeignKey("forecast_runs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("week_number", sa.Integer(), nullable=False),
        sa.Column("week_start", sa.Date(), nullable=False),
        sa.Column("opening_cash", sa.Numeric(18, 2), nullable=False),
        sa.Column("projected_inflows", sa.Numeric(18, 2), nullable=False),
        sa.Column("projected_outflows", sa.Numeric(18, 2), nullable=False),
        sa.Column("net_cash_flow", sa.Numeric(18, 2), nullable=False),
        sa.Column("closing_cash", sa.Numeric(18, 2), nullable=False),
        sa.Column("value_label", sa.String(50), nullable=False, server_default="calculated"),
        sa.Column("contributing_inflow_refs", json_type, nullable=False, server_default=sa.text("'[]'")),
        sa.Column("contributing_outflow_refs", json_type, nullable=False, server_default=sa.text("'[]'")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.CheckConstraint("value_label IN ('observed', 'calculated', 'estimated', 'hypothetical')", name="check_forecast_point_label"),
    )
    op.create_index("idx_forecast_points_run_week", "forecast_points", ["run_id", "week_number"])

    # 12. anomaly_flags
    op.create_table(
        "anomaly_flags",
        sa.Column("id", uuid_type, primary_key=True),
        sa.Column("org_id", uuid_type, sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("source_row_id", uuid_type, sa.ForeignKey("source_rows.id", ondelete="SET NULL"), nullable=True),
        sa.Column("entity_type", sa.String(100), nullable=False),
        sa.Column("entity_id", uuid_type, nullable=True),
        sa.Column("anomaly_type", sa.String(100), nullable=False),
        sa.Column("severity", sa.String(50), nullable=False, server_default="warning"),
        sa.Column("details", json_type, nullable=False, server_default=sa.text("'{}'")),
        sa.Column("status", sa.String(50), nullable=False, server_default="flagged"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.CheckConstraint("severity IN ('info', 'warning', 'critical')", name="check_anomaly_severity"),
        sa.CheckConstraint("status IN ('flagged', 'reviewed', 'resolved', 'ignored')", name="check_anomaly_status"),
    )
    op.create_index("idx_anomaly_flags_org_status", "anomaly_flags", ["org_id", "status"])


def downgrade() -> None:
    op.drop_table("anomaly_flags")
    op.drop_table("forecast_points")
    op.drop_table("forecast_runs")
    op.drop_table("scenario_changes")
    op.drop_table("scenarios")
    op.drop_table("finance_assumptions")
    op.drop_table("payroll_items")
    op.drop_table("invoices")
    op.drop_table("financial_records")
    op.drop_table("source_rows")
    op.drop_table("import_batches")
    op.drop_table("finance_settings")
