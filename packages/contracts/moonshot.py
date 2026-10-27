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
    question_id: str
    prompt: str
    options: List[ClarificationOption] = Field(default_factory=list)
    allows_custom: bool = True

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
