"""Database Layer & Migrations for Moonshot Mode (Range 0200-0299).

Provides SQLite system-of-record storage compatible with PostgreSQL conventions:
- Strict DB-level enforcement of HR-08, HR-09, HR-10, HR-11, HR-12
- Pre-seeded with 4 scoring profiles, criteria, and 12 approved founder cards
- Views: approved_cards and bad_weight_profiles
"""
from __future__ import annotations

import json
import sqlite3
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional
from services.api.app.moonshot.cards import SEED_APPROVED_CARDS, StrategyCard
from services.api.app.moonshot.scoring import SCORING_PROFILES

DEFAULT_DB_PATH = Path("moonshot.db")


def get_connection(db_path: Optional[Path] = None) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path or DEFAULT_DB_PATH))
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: Optional[Path] = None) -> sqlite3.Connection:
    """Initialize Moonshot schema, views, and seed global reference data."""
    conn = get_connection(db_path)
    cur = conn.cursor()

    cur.executescript("""
    -- Global Reference Tables (No org_id, tenancy shared)
    CREATE TABLE IF NOT EXISTS criteria (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        description TEXT NOT NULL,
        how_scored TEXT NOT NULL,
        default_rank INTEGER NOT NULL
    );

    CREATE TABLE IF NOT EXISTS scoring_profiles (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        method TEXT NOT NULL,
        is_default INTEGER DEFAULT 0,
        version INTEGER DEFAULT 1
    );

    CREATE TABLE IF NOT EXISTS scoring_weights (
        profile_id TEXT NOT NULL REFERENCES scoring_profiles(id),
        criterion_id TEXT NOT NULL REFERENCES criteria(id),
        rank_pos INTEGER NOT NULL,
        weight REAL NOT NULL,
        PRIMARY KEY (profile_id, criterion_id)
    );

    CREATE TABLE IF NOT EXISTS strategy_cards (
        id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        summary TEXT NOT NULL,
        lever_type TEXT NOT NULL,
        parameter_template TEXT NOT NULL,
        time_to_signal_days INTEGER NOT NULL,
        cost_to_undo REAL NOT NULL,
        upfront_cost REAL NOT NULL,
        evidence_tier TEXT CHECK(evidence_tier IN ('A', 'B', 'C')),
        source_citation TEXT NOT NULL,
        source_excerpt TEXT NOT NULL,
        source_excerpt_hash TEXT NOT NULL,
        strategic_mechanism TEXT DEFAULT '',
        status TEXT CHECK(status IN ('approved', 'draft', 'archived')),
        reviewer TEXT,
        review_date TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS card_tags (
        id TEXT PRIMARY KEY,
        card_id TEXT NOT NULL REFERENCES strategy_cards(id),
        tag TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS experiment_templates (
        id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        metric TEXT NOT NULL,
        duration_days INTEGER NOT NULL,
        template_body TEXT NOT NULL
    );

    -- Tenant-scoped Moonshot Pipeline Tables
    CREATE TABLE IF NOT EXISTS moonshot_requests (
        id TEXT PRIMARY KEY,
        org_id TEXT NOT NULL,
        user_id TEXT NOT NULL,
        decision_run_id TEXT,
        raw_text TEXT NOT NULL,
        status TEXT CHECK(status IN ('intake', 'needs_input', 'running', 'completed', 'failed')) DEFAULT 'intake',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS goals (
        id TEXT PRIMARY KEY,
        request_id TEXT NOT NULL REFERENCES moonshot_requests(id),
        metric TEXT,
        target TEXT,
        deadline TEXT,
        domain TEXT,
        structured_summary TEXT
    );

    CREATE TABLE IF NOT EXISTS request_constraints (
        id TEXT PRIMARY KEY,
        request_id TEXT NOT NULL REFERENCES moonshot_requests(id),
        horizon_weeks INTEGER NOT NULL,
        budget_cap REAL NOT NULL,
        team_size INTEGER NOT NULL,
        risk_tolerance TEXT CHECK(risk_tolerance IN ('low', 'medium', 'high')),
        cash_floor_weeks INTEGER NOT NULL,
        status TEXT CHECK(status IN ('confirmed', 'assumed_default')) DEFAULT 'confirmed'
    );

    CREATE TABLE IF NOT EXISTS hard_limits (
        id TEXT PRIMARY KEY,
        request_id TEXT NOT NULL REFERENCES moonshot_requests(id),
        description TEXT NOT NULL,
        limit_type TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS clarification_questions (
        id TEXT PRIMARY KEY,
        request_id TEXT NOT NULL REFERENCES moonshot_requests(id),
        field_name TEXT NOT NULL,
        question TEXT NOT NULL,
        tappable_options TEXT NOT NULL,
        round_number INTEGER NOT NULL,
        answer TEXT
    );

    CREATE TABLE IF NOT EXISTS goal_assumptions (
        id TEXT PRIMARY KEY,
        request_id TEXT NOT NULL REFERENCES moonshot_requests(id),
        text TEXT NOT NULL,
        importance REAL NOT NULL,
        is_critical INTEGER NOT NULL,
        category TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS candidate_strategies (
        id TEXT PRIMARY KEY,
        request_id TEXT NOT NULL REFERENCES moonshot_requests(id),
        card_id TEXT NOT NULL REFERENCES strategy_cards(id),
        match_reason TEXT,
        fit_score REAL
    );

    CREATE TABLE IF NOT EXISTS gate_results (
        id TEXT PRIMARY KEY,
        request_id TEXT NOT NULL REFERENCES moonshot_requests(id),
        candidate_id TEXT NOT NULL REFERENCES candidate_strategies(id),
        passed INTEGER NOT NULL,
        breached_gates TEXT NOT NULL,
        warnings TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS strategy_rankings (
        id TEXT PRIMARY KEY,
        request_id TEXT NOT NULL REFERENCES moonshot_requests(id),
        candidate_id TEXT NOT NULL REFERENCES candidate_strategies(id),
        profile_id TEXT NOT NULL,
        weighted_sum REAL NOT NULL,
        multiplier REAL NOT NULL,
        final_score REAL NOT NULL,
        position INTEGER NOT NULL
    );

    CREATE TABLE IF NOT EXISTS reports (
        id TEXT PRIMARY KEY,
        request_id TEXT NOT NULL REFERENCES moonshot_requests(id),
        org_id TEXT NOT NULL,
        user_id TEXT NOT NULL,
        report_markdown TEXT NOT NULL,
        sensitivity_verdict TEXT NOT NULL,
        disclaimer_verified INTEGER CHECK(disclaimer_verified = 1),
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS claims (
        id TEXT PRIMARY KEY,
        report_id TEXT NOT NULL REFERENCES reports(id),
        text TEXT NOT NULL,
        tag TEXT CHECK(tag IN ('cited', 'computed', 'inferred', 'commentary')),
        status TEXT CHECK(status IN ('verified', 'warning', 'unverified', 'failed'))
    );

    -- Views
    DROP VIEW IF EXISTS approved_cards;
    CREATE VIEW approved_cards AS
    SELECT * FROM strategy_cards
    WHERE status = 'approved' AND reviewer IS NOT NULL AND review_date IS NOT NULL;

    DROP VIEW IF EXISTS bad_weight_profiles;
    CREATE VIEW bad_weight_profiles AS
    SELECT profile_id, ROUND(SUM(weight), 4) as total
    FROM scoring_weights
    GROUP BY profile_id
    HAVING ABS(total - 1.0) > 0.001;
    """)

    # Seed Criteria
    criteria_data = [
        ("fit", "Strategic Fit", "Assumption tree coverage with double-weight for critical assumptions", "inferred", 1),
        ("cash", "Cash Impact", "Min-max normalized mean of ending and minimum cash deltas", "computed", 2),
        ("signal", "Time to Signal", "Days to first observable signal from strategy", "cited", 3),
        ("reversibility", "Reversibility", "Cost to undo relative to budget cap", "cited", 4),
    ]
    cur.executemany("INSERT OR IGNORE INTO criteria VALUES (?, ?, ?, ?, ?)", criteria_data)

    # Seed Profiles
    profiles_data = [
        ("roc_default", "Rank Order Centroid (Default)", "roc", 1, 1),
        ("rank_sum", "Rank-Sum Weighting", "rank_sum", 0, 1),
        ("equal", "Equal Weighting", "equal", 0, 1),
        ("roc_low_risk", "ROC Low Risk Profile", "roc", 0, 1),
    ]
    cur.executemany("INSERT OR IGNORE INTO scoring_profiles VALUES (?, ?, ?, ?, ?)", profiles_data)

    # Seed Weights
    weights_rows = []
    for prof_id, weights in SCORING_PROFILES.items():
        for rank_idx, (crit_id, weight) in enumerate(weights.items(), 1):
            weights_rows.append((prof_id, crit_id, rank_idx, weight))
    cur.executemany("INSERT OR IGNORE INTO scoring_weights VALUES (?, ?, ?, ?)", weights_rows)

    # Migration check for existing DBs
    try:
        cur.execute("ALTER TABLE strategy_cards ADD COLUMN strategic_mechanism TEXT DEFAULT ''")
    except sqlite3.OperationalError:
        pass

    # Seed 12 Approved Founder Cards
    for card in SEED_APPROVED_CARDS:
        cur.execute(
            """INSERT INTO strategy_cards
            (id, title, summary, lever_type, parameter_template, time_to_signal_days, cost_to_undo, upfront_cost,
             evidence_tier, source_citation, source_excerpt, source_excerpt_hash, strategic_mechanism, status, reviewer, review_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                title=excluded.title,
                summary=excluded.summary,
                lever_type=excluded.lever_type,
                parameter_template=excluded.parameter_template,
                time_to_signal_days=excluded.time_to_signal_days,
                cost_to_undo=excluded.cost_to_undo,
                upfront_cost=excluded.upfront_cost,
                evidence_tier=excluded.evidence_tier,
                source_citation=excluded.source_citation,
                source_excerpt=excluded.source_excerpt,
                source_excerpt_hash=excluded.source_excerpt_hash,
                strategic_mechanism=excluded.strategic_mechanism,
                status=excluded.status,
                reviewer=excluded.reviewer,
                review_date=excluded.review_date""",
            (
                str(card.id),
                card.title,
                card.summary,
                card.lever_type,
                json.dumps(card.parameter_template),
                card.time_to_signal_days,
                card.cost_to_undo,
                card.upfront_cost,
                card.evidence_tier,
                card.source_citation,
                card.source_excerpt,
                card.source_excerpt_hash,
                card.strategic_mechanism,
                card.status,
                card.reviewer,
                str(card.review_date),
            ),
        )
        for tag in card.tags:
            cur.execute(
                "INSERT OR IGNORE INTO card_tags VALUES (?, ?, ?)",
                (str(uuid.uuid4()), str(card.id), tag),
            )

    conn.commit()
    return conn
