"""Shared Moonshot Mode Contract (Part A6).
Canonical interface between Moonshot Mode (Aleena) and Chatbot (Aroon).
"""
from typing import Any, AsyncGenerator, Dict, List, Literal, Optional, Protocol, Union
from uuid import UUID, uuid4
from pydantic import BaseModel, Field

from packages.contracts.envelope import ToolResultEnvelope

class ClarificationOption(BaseModel):
    id: str
    label: str

class ClarificationQuestion(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    question_id: Optional[str] = None
    prompt: Optional[str] = None
    field_name: Optional[str] = None
    question: Optional[str] = None
    tappable_options: List[str] = Field(default_factory=list)
    options: List[ClarificationOption] = Field(default_factory=list)
    allows_custom: bool = True
    round_number: int = 1

    def model_post_init(self, __context: Any) -> None:
        if self.field_name and not self.question_id:
            self.question_id = self.field_name
        elif self.question_id and not self.field_name:
            self.field_name = self.question_id

        if self.question and not self.prompt:
            self.prompt = self.question
        elif self.prompt and not self.question:
            self.question = self.prompt

        if self.tappable_options and not self.options:
            self.options = [ClarificationOption(id=opt, label=opt) for opt in self.tappable_options]
        elif self.options and not self.tappable_options:
            self.tappable_options = [opt.label for opt in self.options]

class NeedsInputResult(BaseModel):
    kind: Literal["needs_input"] = "needs_input"
    request_id: UUID
    round_number: int
    questions: List[ClarificationQuestion]

class RankedStrategy(BaseModel):
    strategy_id: UUID
    name: str
    description: str
    fit_score: float
    reversibility: str
    cash_impact_expected: str
    cash_impact_worst: str
    cfo_run_id: UUID
    rank: int

class FailedGateItem(BaseModel):
    strategy_id: UUID
    name: str
    failed_gate: str
    reason: str

class MoonshotReport(BaseModel):
    report_id: UUID = Field(default_factory=uuid4)
    goal: str
    constraints: List[Dict[str, Any]] = Field(default_factory=list)
    what_must_be_true: List[str] = Field(default_factory=list)
    top_strategies: List[RankedStrategy] = Field(default_factory=list)
    failed_gates: List[FailedGateItem] = Field(default_factory=list)
    skeptic_section: str
    experiments_30d: List[Dict[str, Any]] = Field(default_factory=list)
    weight_sensitivity: str
    assumptions_limits: List[str] = Field(default_factory=list)
    disclaimer_present: bool = True
    claims_count: int = 0

class StageEvent(BaseModel):
    stage_number: int
    stage_name: str
    status: Literal["started", "completed", "failed"]

class MoonshotWorkflow(Protocol):
    """Protocol for Aleena's MoonshotWorkflow."""
    async def run(
        self,
        org_id: UUID,
        user_id: UUID,
        goal: str,
        constraints: Optional[Dict[str, Any]] = None,
        answers: Optional[Dict[str, str]] = None,
    ) -> Union[NeedsInputResult, MoonshotReport]:
        ...

    async def stream_stages(
        self, org_id: UUID, goal: str
    ) -> AsyncGenerator[StageEvent, None]:
        ...

class FakeMoonshotWorkflow:
    """Runnable fake for standalone Chatbot testing."""
    def __init__(self):
        self.pending_rounds: Dict[str, int] = {}

    async def stream_stages(self, org_id: UUID, goal: str) -> AsyncGenerator[StageEvent, None]:
        stages = [
            (1, "Intake & Safety Check"),
            (2, "Constraint Extraction & Decomposition"),
            (3, "Strategy Card Retrieval & Filtering"),
            (4, "CFO Simulation & Levers"),
            (5, "Gating, Scoring & Stress-Testing"),
            (6, "Report Assembly & Skeptic Analysis"),
        ]
        for num, name in stages:
            yield StageEvent(stage_number=num, stage_name=name, status="completed")

    async def run(
        self,
        org_id: UUID,
        user_id: UUID,
        goal: str,
        constraints: Optional[Dict[str, Any]] = None,
        answers: Optional[Dict[str, str]] = None,
    ) -> Union[NeedsInputResult, MoonshotReport]:
        # If user hasn't provided answers yet, trigger one round of tappable clarification options
        if not answers:
            req_id = uuid4()
            return NeedsInputResult(
                request_id=req_id,
                round_number=1,
                questions=[
                    ClarificationQuestion(
                        question_id="risk_tolerance",
                        prompt="What is your maximum risk tolerance for operational changes?",
                        options=[
                            ClarificationOption(id="conservative", label="Conservative (Maintain 12w runway floor)"),
                            ClarificationOption(id="moderate", label="Moderate (Accept short-term 8w dip)"),
                            ClarificationOption(id="aggressive", label="Aggressive (Growth prioritized over cash reserve)"),
                        ],
                    ),
                    ClarificationQuestion(
                        question_id="budget_cap",
                        prompt="What is your hard capital expenditure / investment cap?",
                        options=[
                            ClarificationOption(id="cap_25k", label="$25,000 Cap"),
                            ClarificationOption(id="cap_50k", label="$50,000 Cap"),
                            ClarificationOption(id="cap_100k", label="$100,000 Cap"),
                        ],
                    ),
                ],
            )

        # Once answers are provided, generate complete 9-section Moonshot Report
        cfo_run_1 = uuid4()
        cfo_run_2 = uuid4()
        top_strats = [
            RankedStrategy(
                strategy_id=uuid4(),
                name="Performance-Based Retainer Shift",
                description="Convert tier-1 clients to a 50% upfront deposit + performance bonus cadence.",
                fit_score=88.5,
                reversibility="High (30d notice)",
                cash_impact_expected="+$35,000.00 cash floor improvement in 6 weeks",
                cash_impact_worst="+$10,000.00 floor improvement (delayed adoption)",
                cfo_run_id=cfo_run_1,
                rank=1,
            ),
            RankedStrategy(
                strategy_id=uuid4(),
                name="Productized Discovery Sprint",
                description="Sell mandatory 2-week technical discovery audits paid 100% upfront before development.",
                fit_score=82.0,
                reversibility="Medium (60d contract terms)",
                cash_impact_expected="+$28,000.00 upfront working capital",
                cash_impact_worst="+$12,000.00 upfront working capital",
                cfo_run_id=cfo_run_2,
                rank=2,
            ),
        ]
        failed_gates = [
            FailedGateItem(
                strategy_id=uuid4(),
                name="Aggressive Headcount Expansion",
                failed_gate="Cash Floor Breach",
                reason="Breaches the 12-week minimum cash reserve in week 8 under worst-case collection delays.",
            )
        ]

        return MoonshotReport(
            report_id=uuid4(),
            goal=goal,
            constraints=[
                {"name": "Cash Floor", "rule": ">= 12 weeks committed outflow", "status": "passed"},
                {"name": "Execution Horizon", "rule": "<= 90 days", "status": "passed"},
            ],
            what_must_be_true=[
                "At least 2 clients accept 50% upfront payment terms",
                "Project delivery margin remains above 45%",
            ],
            top_strategies=top_strats,
            failed_gates=failed_gates,
            skeptic_section=(
                "Pre-Mortem & Skeptic Analysis: Client churn may spike if terms are changed without "
                "offsetting deliverables. Base rates indicate 18% client hesitation on altered billing models."
            ),
            experiments_30d=[
                {"day_range": "Day 1-10", "task": "Pitch discovery sprint model to next 2 prospective clients"},
                {"day_range": "Day 11-30", "task": "Measure conversion rate against legacy hourly contract close rate"},
            ],
            weight_sensitivity="Recommendation is robust across both Balanced and Conservative scoring weight profiles.",
            assumptions_limits=[
                "Simulated against baseline cash $120,000.00",
                "Client payments follow standard 30d terms unless explicitly modified",
            ],
            disclaimer_present=True,
            claims_count=12,
        )


# --- Moonshot Pipeline Models (Aleena Engine) ---
class FixedConstraints(BaseModel):
    horizon_weeks: int = Field(default=26, ge=1, le=104)
    budget_cap: float = Field(default=50_000.0, ge=0.0)
    team_size: int = Field(default=4, ge=1)
    risk_tolerance: Literal["low", "medium", "high"] = "medium"
    cash_floor_weeks: int = Field(default=12, ge=1)
    status: Literal["confirmed", "assumed_default"] = "confirmed"

class UserHardLimit(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    description: str
    limit_type: str

class GoalAssumption(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    text: str
    importance: float = Field(ge=0.0, le=100.0)
    is_critical: bool = False
    category: Literal["demand", "execution", "financial", "market"] = "demand"

class CandidateStrategy(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    card_id: UUID = Field(default_factory=uuid4)
    title: str
    summary: str = ""
    lever_type: str
    time_to_signal_days: int
    cost_to_undo: float
    upfront_cost: float
    evidence_tier: Literal["A", "B", "C"] = "B"
    assumptions_addressed: List[UUID] = Field(default_factory=list)
    parameter_template: Dict[str, Any] = Field(default_factory=dict)
    source_quote: str = ""
    source_quote_hash: str = ""
    source_citation: str = ""
    strategic_mechanism: str = ""

class GateResult(BaseModel):
    candidate_id: UUID
    passed: bool
    breached_gates: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)

class CriterionScore(BaseModel):
    criterion: Literal["fit", "cash", "signal", "reversibility"]
    raw_value: float
    normalized_score: float = Field(ge=0.0, le=100.0)
    tag: Literal["cited", "computed", "inferred", "commentary"]

class StrategyRanking(BaseModel):
    candidate_id: UUID
    profile_name: str
    weighted_sum: float
    multiplier: float
    final_score: float
    position: int

class SensitivityCheckResult(BaseModel):
    top_candidate_id: UUID
    is_robust: bool
    summary: str
    profile_top_picks: Dict[str, UUID]

class MoonshotReportSummary(BaseModel):
    report_id: UUID
    goal_statement: str
    constraints: FixedConstraints
    ranked_strategies: List[Dict[str, Any]]
    flagged_strategies: List[Dict[str, Any]]
    sensitivity: SensitivityCheckResult
    skeptic_section: Dict[str, Any]
    disclaimer: str = "Decision support, not financial advice. Forecasts depend on the assumptions shown and are not guaranteed predictions."
    disclaimer_verified: bool = True
