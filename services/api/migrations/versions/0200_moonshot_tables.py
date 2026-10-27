"""Moonshot Mode Schema (0200-0299).
Alembic migration revision: 0200_moonshot_tables
Revises: None (standalone module migration range 0200-0299 for Aleena)
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0200_moonshot_tables"
down_revision = None
branch_labels = ("moonshot",)
depends_on = None


def upgrade() -> None:
    # 1. criteria
    op.create_table(
        "criteria",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("how_scored", sa.Text(), nullable=False),
        sa.Column("default_rank", sa.Integer(), nullable=False),
    )

    # 2. scoring_profiles
    op.create_table(
        "scoring_profiles",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("method", sa.String(32), nullable=False),
        sa.Column("is_default", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
    )

    # 3. scoring_weights
    op.create_table(
        "scoring_weights",
        sa.Column("profile_id", sa.String(64), sa.ForeignKey("scoring_profiles.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("criterion_id", sa.String(64), sa.ForeignKey("criteria.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("rank_pos", sa.Integer(), nullable=False),
        sa.Column("weight", sa.Float(), nullable=False),
    )

    # 4. strategy_cards
    op.create_table(
        "strategy_cards",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("lever_type", sa.String(64), nullable=False),
        sa.Column("parameter_template", sa.Text(), nullable=False),
        sa.Column("time_to_signal_days", sa.Integer(), nullable=False),
        sa.Column("cost_to_undo", sa.Float(), nullable=False),
        sa.Column("upfront_cost", sa.Float(), nullable=False),
        sa.Column("evidence_tier", sa.String(8), sa.CheckConstraint("evidence_tier IN ('A', 'B', 'C')"), nullable=False),
        sa.Column("source_citation", sa.Text(), nullable=False),
        sa.Column("source_excerpt", sa.Text(), nullable=False),
        sa.Column("source_excerpt_hash", sa.String(64), nullable=False),
        sa.Column("strategic_mechanism", sa.Text(), server_default="", nullable=False),
        sa.Column("status", sa.String(16), sa.CheckConstraint("status IN ('approved', 'draft', 'archived')"), nullable=False),
        sa.Column("reviewer", sa.String(128), nullable=True),
        sa.Column("review_date", sa.String(32), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False),
    )

    # 5. card_tags
    op.create_table(
        "card_tags",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("card_id", sa.String(64), sa.ForeignKey("strategy_cards.id", ondelete="CASCADE"), nullable=False),
        sa.Column("tag", sa.String(64), nullable=False),
    )
    op.create_index("idx_card_tags_card", "card_tags", ["card_id"])

    # 6. experiment_templates
    op.create_table(
        "experiment_templates",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("metric", sa.String(128), nullable=False),
        sa.Column("duration_days", sa.Integer(), nullable=False),
        sa.Column("template_body", sa.Text(), nullable=False),
    )

    # 7. moonshot_requests
    op.create_table(
        "moonshot_requests",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("org_id", sa.String(64), nullable=False),
        sa.Column("user_id", sa.String(64), nullable=False),
        sa.Column("decision_run_id", sa.String(64), nullable=True),
        sa.Column("raw_text", sa.Text(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False),
    )

    # 8. goals
    op.create_table(
        "goals",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("request_id", sa.String(64), sa.ForeignKey("moonshot_requests.id", ondelete="CASCADE"), nullable=False),
        sa.Column("statement", sa.Text(), nullable=False),
        sa.Column("target_metric", sa.String(128), nullable=True),
        sa.Column("target_value", sa.Float(), nullable=True),
    )

    # 9. request_constraints
    op.create_table(
        "request_constraints",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("request_id", sa.String(64), sa.ForeignKey("moonshot_requests.id", ondelete="CASCADE"), nullable=False),
        sa.Column("horizon_weeks", sa.Integer(), nullable=False),
        sa.Column("budget_cap", sa.Float(), nullable=False),
        sa.Column("team_size", sa.Integer(), nullable=False),
        sa.Column("risk_tolerance", sa.String(32), nullable=False),
        sa.Column("cash_floor_weeks", sa.Integer(), nullable=False),
    )

    # 10. hard_limits
    op.create_table(
        "hard_limits",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("request_id", sa.String(64), sa.ForeignKey("moonshot_requests.id", ondelete="CASCADE"), nullable=False),
        sa.Column("limit_type", sa.String(64), nullable=False),
        sa.Column("limit_value", sa.Float(), nullable=False),
    )

    # 11. goal_assumptions
    op.create_table(
        "goal_assumptions",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("request_id", sa.String(64), sa.ForeignKey("moonshot_requests.id", ondelete="CASCADE"), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("category", sa.String(64), nullable=False),
        sa.Column("importance", sa.Float(), nullable=False),
        sa.Column("is_critical", sa.Boolean(), nullable=False),
    )

    # 12. candidate_strategies
    op.create_table(
        "candidate_strategies",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("request_id", sa.String(64), sa.ForeignKey("moonshot_requests.id", ondelete="CASCADE"), nullable=False),
        sa.Column("card_id", sa.String(64), nullable=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("lever_type", sa.String(64), nullable=False),
        sa.Column("time_to_signal_days", sa.Integer(), nullable=False),
        sa.Column("cost_to_undo", sa.Float(), nullable=False),
        sa.Column("upfront_cost", sa.Float(), nullable=False),
        sa.Column("evidence_tier", sa.String(8), nullable=False),
        sa.Column("cfo_run_id", sa.String(64), nullable=True),
        sa.Column("expected_end_cash", sa.Float(), nullable=False),
        sa.Column("min_cash", sa.Float(), nullable=False),
        sa.Column("runway_weeks", sa.Integer(), nullable=False),
    )

    # 13. gate_results
    op.create_table(
        "gate_results",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("candidate_id", sa.String(64), sa.ForeignKey("candidate_strategies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("gate_name", sa.String(32), nullable=False),
        sa.Column("passed", sa.Boolean(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
    )

    # 14. strategy_rankings
    op.create_table(
        "strategy_rankings",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("request_id", sa.String(64), sa.ForeignKey("moonshot_requests.id", ondelete="CASCADE"), nullable=False),
        sa.Column("candidate_id", sa.String(64), sa.ForeignKey("candidate_strategies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("profile_id", sa.String(64), nullable=False),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("rank_pos", sa.Integer(), nullable=False),
    )

    # 15. reports
    op.create_table(
        "reports",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("request_id", sa.String(64), sa.ForeignKey("moonshot_requests.id", ondelete="CASCADE"), nullable=False),
        sa.Column("report_markdown", sa.Text(), nullable=False),
        sa.Column("disclaimer_verified", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False),
    )

    # 16. claims
    op.create_table(
        "claims",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("report_id", sa.String(64), sa.ForeignKey("reports.id", ondelete="CASCADE"), nullable=False),
        sa.Column("statement", sa.Text(), nullable=False),
        sa.Column("tag", sa.String(32), sa.CheckConstraint("tag IN ('cited', 'computed', 'inferred', 'commentary')"), nullable=False),
        sa.Column("verified", sa.Boolean(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
    )

    # Views (HR-11, HR-12)
    op.execute("""
        CREATE VIEW approved_cards AS
        SELECT * FROM strategy_cards
        WHERE status = 'approved';
    """)

    op.execute("""
        CREATE VIEW bad_weight_profiles AS
        SELECT profile_id, SUM(weight) as total_weight
        FROM scoring_weights
        GROUP BY profile_id
        HAVING ABS(SUM(weight) - 1.0) > 0.001;
    """)


def downgrade() -> None:
    op.execute("DROP VIEW IF EXISTS bad_weight_profiles")
    op.execute("DROP VIEW IF EXISTS approved_cards")
    op.drop_table("claims")
    op.drop_table("reports")
    op.drop_table("strategy_rankings")
    op.drop_table("gate_results")
    op.drop_table("candidate_strategies")
    op.drop_table("goal_assumptions")
    op.drop_table("hard_limits")
    op.drop_table("request_constraints")
    op.drop_table("goals")
    op.drop_table("moonshot_requests")
    op.drop_table("experiment_templates")
    op.drop_table("card_tags")
    op.drop_table("strategy_cards")
    op.drop_table("scoring_weights")
    op.drop_table("scoring_profiles")
    op.drop_table("criteria")
