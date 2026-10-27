"""Chatbot Core Schema (0300-0399).
Alembic migration revision: 0300_chat_core
Revises: 0099_core_frozen (once published by Sharjeel; nullable until tag exists)
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0300_chat_core"
down_revision = None  # Rebase onto 0099 when foundation-v1 is tagged
branch_labels = None
depends_on = None

def upgrade() -> None:
    # 1. agents
    op.create_table(
        "agents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("key", sa.String(64), unique=True, nullable=False),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("system_prompt", sa.Text(), nullable=False),
        sa.Column("allowed_tools", postgresql.JSONB(), server_default=sa.text("'[]'"), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False),
    )

    # 2. conversations
    op.create_table(
        "conversations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("org_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("agent_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("agents.id"), nullable=False),
        sa.Column("title", sa.String(255), server_default="New Conversation", nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False),
    )
    op.create_index("idx_conversations_org_user", "conversations", ["org_id", "user_id"])

    # 3. messages
    op.create_table(
        "messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("org_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("conversation_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("sender", sa.String(16), sa.CheckConstraint("sender IN ('user', 'assistant', 'system')"), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("token_count", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False),
    )
    op.create_index("idx_messages_org_conv", "messages", ["org_id", "conversation_id"])

    # 4. tool_calls
    op.create_table(
        "tool_calls",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("org_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("message_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("messages.id", ondelete="CASCADE"), nullable=False),
        sa.Column("decision_run_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("tool_name", sa.String(128), nullable=False),
        sa.Column("arguments", postgresql.JSONB(), nullable=False),
        sa.Column("status", sa.String(32), sa.CheckConstraint("status IN ('started', 'completed', 'failed', 'timeout')"), nullable=False),
        sa.Column("result_status", sa.String(32), sa.CheckConstraint("result_status IN ('ok', 'warning', 'failed')"), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False),
    )
    op.create_index("idx_tool_calls_org_decision", "tool_calls", ["org_id", "decision_run_id"])

    # 5. action_proposals
    op.create_table(
        "action_proposals",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("org_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("conversation_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("conversations.id"), nullable=False),
        sa.Column("action_type", sa.String(64), nullable=False),
        sa.Column("payload", postgresql.JSONB(), nullable=False),
        sa.Column("risk_level", sa.String(16), sa.CheckConstraint("risk_level IN ('low', 'medium', 'high')"), nullable=False),
        sa.Column("status", sa.String(32), sa.CheckConstraint("status IN ('proposed', 'validated', 'awaiting_approval', 'approved', 'applied', 'rejected', 'expired', 'failed')"), nullable=False),
        sa.Column("proposed_by_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("approved_by_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("executed_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("rejection_reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False),
    )
    op.create_index("idx_action_proposals_org_status", "action_proposals", ["org_id", "status"])

    # 6. voice_transcripts
    op.create_table(
        "voice_transcripts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("org_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("conversation_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("conversations.id"), nullable=False),
        sa.Column("audio_duration_sec", sa.Numeric(8, 2), nullable=False),
        sa.Column("raw_transcript", sa.Text(), nullable=False),
        sa.Column("edited_transcript", sa.Text(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False),
    )
    op.create_index("idx_voice_transcripts_org", "voice_transcripts", ["org_id"])

    # 7. documents
    op.create_table(
        "documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("org_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("filename", sa.String(255), nullable=False),
        sa.Column("file_size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("mime_type", sa.String(128), nullable=False),
        sa.Column("content_hash", sa.String(64), nullable=False),
        sa.Column("storage_path", sa.Text(), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.UniqueConstraint("org_id", "content_hash", name="uq_documents_org_hash"),
    )
    op.create_index("idx_documents_org", "documents", ["org_id"])

    # 8. ingestion_jobs
    op.create_table(
        "ingestion_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("org_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("documents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.String(32), sa.CheckConstraint("status IN ('pending', 'processing', 'completed', 'failed')"), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("progress_pct", sa.Integer(), server_default="0", nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False),
    )
    op.create_index("idx_ingestion_jobs_org_status", "ingestion_jobs", ["org_id", "status"])

    # 9. document_chunks
    op.create_table(
        "document_chunks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("org_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("documents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("page_number", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("token_count", sa.Integer(), nullable=False),
        sa.Column("embedding", sa.NullType(), nullable=True), # pgvector vector(1536)
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False),
    )
    op.create_index("idx_document_chunks_org", "document_chunks", ["org_id", "document_id"])

    # 10. web_sources
    op.create_table(
        "web_sources",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("org_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("snippet", sa.Text(), nullable=False),
        sa.Column("retrieved_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False),
    )
    op.create_index("idx_web_sources_org", "web_sources", ["org_id"])

    # 11. memories
    op.create_table(
        "memories",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("org_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("category", sa.String(64), nullable=False),
        sa.Column("key", sa.String(128), nullable=False),
        sa.Column("value", sa.Text(), nullable=False),
        sa.Column("status", sa.String(32), sa.CheckConstraint("status IN ('proposed', 'confirmed', 'rejected', 'archived')"), nullable=False),
        sa.Column("source_message_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False),
    )
    op.create_index("idx_memories_org_user", "memories", ["org_id", "user_id", "status"])

    # 12. feedback
    op.create_table(
        "feedback",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("org_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("message_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("messages.id"), nullable=False),
        sa.Column("score", sa.Integer(), sa.CheckConstraint("score IN (-1, 1)"), nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("eval_case_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False),
    )
    op.create_index("idx_feedback_org", "feedback", ["org_id"])

    # 13. eval_cases
    op.create_table(
        "eval_cases",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("category", sa.String(64), nullable=False),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("expected_tools", postgresql.JSONB(), server_default=sa.text("'[]'"), nullable=False),
        sa.Column("expected_facts", postgresql.JSONB(), server_default=sa.text("'[]'"), nullable=False),
        sa.Column("expected_risk", sa.String(16), server_default="low", nullable=False),
        sa.Column("active", sa.Boolean(), server_default=sa.text("TRUE"), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False),
    )

    # 14. eval_runs
    op.create_table(
        "eval_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("model_name", sa.String(128), nullable=False),
        sa.Column("git_commit", sa.String(64), nullable=True),
        sa.Column("started_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("completed_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("summary_metrics", postgresql.JSONB(), server_default=sa.text("'{}'"), nullable=False),
    )

    # 15. eval_results
    op.create_table(
        "eval_results",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("eval_run_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("eval_runs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("eval_case_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("eval_cases.id"), nullable=False),
        sa.Column("tool_choice_score", sa.Numeric(5, 2), nullable=False),
        sa.Column("fact_score", sa.Numeric(5, 2), nullable=False),
        sa.Column("citation_score", sa.Numeric(5, 2), nullable=False),
        sa.Column("latency_ms", sa.Integer(), nullable=False),
        sa.Column("passed", sa.Boolean(), nullable=False),
        sa.Column("details", postgresql.JSONB(), server_default=sa.text("'{}'"), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False),
    )

    # 16. dashboards
    op.create_table(
        "dashboards",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("org_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(128), server_default="Main CFO Dashboard", nullable=False),
        sa.Column("layout", postgresql.JSONB(), server_default=sa.text("'[]'"), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False),
    )
    op.create_index("idx_dashboards_org", "dashboards", ["org_id"])

    # 17. dashboard_widgets
    op.create_table(
        "dashboard_widgets",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("org_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("dashboard_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("dashboards.id", ondelete="CASCADE"), nullable=False),
        sa.Column("widget_type", sa.String(64), nullable=False),
        sa.Column("config", postgresql.JSONB(), server_default=sa.text("'{}'"), nullable=False),
        sa.Column("position_idx", sa.Integer(), server_default="0", nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False),
    )
    op.create_index("idx_dashboard_widgets_org", "dashboard_widgets", ["org_id", "dashboard_id"])

    # 18. verification_checks
    op.create_table(
        "verification_checks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("org_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("decision_run_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("message_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("messages.id"), nullable=False),
        sa.Column("check_type", sa.String(32), nullable=False),
        sa.Column("status", sa.String(16), sa.CheckConstraint("status IN ('passed', 'failed', 'warning')"), nullable=False),
        sa.Column("details", postgresql.JSONB(), server_default=sa.text("'{}'"), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False),
    )
    op.create_index("idx_verification_checks_org_decision", "verification_checks", ["org_id", "decision_run_id"])

def downgrade() -> None:
    for tbl in [
        "verification_checks", "dashboard_widgets", "dashboards", "eval_results",
        "eval_runs", "eval_cases", "feedback", "memories", "web_sources",
        "document_chunks", "ingestion_jobs", "documents", "voice_transcripts",
        "action_proposals", "tool_calls", "messages", "conversations", "agents",
    ]:
        op.drop_table(tbl)
