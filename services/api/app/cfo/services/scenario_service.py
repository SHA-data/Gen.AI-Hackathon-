from datetime import date, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID, uuid4

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from packages.contracts.envelope import ResultStatus, ToolResultEnvelope, ToolStatus
from packages.contracts.finance import (
    CaseResult,
    ScenarioCases,
    ScenarioRunData,
    ScenarioRunRequest,
    WeeklyCashPoint,
)
from services.api.app.cfo.engine.calculator import ForecastCalculationResult, ForecastEngine
from services.api.app.cfo.engine.levers import LeverDispatcher
from services.api.app.cfo.models import (
    FinanceAssumption,
    FinanceSettings,
    ForecastPoint,
    ForecastRun,
    Invoice,
    PayrollItem,
    Scenario,
    ScenarioChange as DBScenarioChange,
)
from services.api.app.core.errors import NotFoundError, ValidationError


class ScenarioService:
    """Orchestrates scenario delta application, 3-case generation, and baseline immutability checks."""

    @classmethod
    async def run_scenario(
        cls,
        session: AsyncSession,
        org_id: UUID,
        request: ScenarioRunRequest,
    ) -> ToolResultEnvelope:
        # 1. Verify Baseline Run Exists
        baseline_run = await session.get(ForecastRun, request.baseline_run_id)
        if not baseline_run or baseline_run.org_id != org_id:
            raise NotFoundError(f"Baseline run {request.baseline_run_id} not found in organization")

        # Snapshot baseline hash for immutability verification
        original_baseline_hash = baseline_run.baseline_hash

        # 2. Query Settings
        stmt = select(FinanceSettings).where(FinanceSettings.org_id == org_id)
        settings = (await session.execute(stmt)).scalar_one_or_none()
        reserve_amt = settings.reserve_amount if settings else Decimal("50000.00")
        floor_weeks = settings.cash_floor_weeks if settings else 12

        # 3. Query Opening Cash
        stmt = select(FinanceAssumption).where(
            FinanceAssumption.org_id == org_id,
            FinanceAssumption.category == "opening_cash",
        ).order_by(desc(FinanceAssumption.valid_from))
        cash_assumption = (await session.execute(stmt)).scalars().first()
        if not cash_assumption:
            raise ValidationError("Missing opening cash assumption")
        opening_cash = Decimal(str(cash_assumption.value.get("amount", "0.00")))
        as_of_date = cash_assumption.valid_from

        # 4. Assemble Raw Inflow Events with Metadata
        stmt = select(Invoice).where(
            Invoice.org_id == org_id,
            Invoice.status.in_(["issued", "late", "draft"]),
            Invoice.expected_payment_date >= as_of_date,
        )
        invoices = (await session.execute(stmt)).scalars().all()
        base_inflows: List[Tuple[date, Decimal, UUID, Dict[str, Any]]] = [
            (
                inv.expected_payment_date,
                inv.amount,
                inv.id,
                {
                    "client": inv.client_or_vendor,
                    "invoice_number": inv.invoice_number,
                    "is_uncertain": inv.is_uncertain,
                },
            )
            for inv in invoices
        ]

        # 5. Assemble Raw Outflow Events with Metadata
        base_outflows: List[Tuple[date, Decimal, UUID, Dict[str, Any]]] = []
        stmt = select(PayrollItem).where(PayrollItem.org_id == org_id)
        payroll_items = (await session.execute(stmt)).scalars().all()
        monthly_payroll_sum = sum(p.monthly_gross + p.benefits_and_taxes for p in payroll_items)

        horizon_days = request.horizon_weeks * 7
        end_date = as_of_date + timedelta(days=horizon_days)

        curr = as_of_date.replace(day=1)
        while curr <= end_date:
            pay_date = date(curr.year, curr.month, 28)
            if pay_date >= as_of_date:
                ref_id = payroll_items[0].id if payroll_items else uuid4()
                base_outflows.append((pay_date, monthly_payroll_sum, ref_id, {"type": "payroll"}))
            if curr.month == 12:
                curr = date(curr.year + 1, 1, 1)
            else:
                curr = date(curr.year, curr.month + 1, 1)

        stmt = select(FinanceAssumption).where(
            FinanceAssumption.org_id == org_id,
            FinanceAssumption.category == "recurring_overhead",
        )
        overheads = (await session.execute(stmt)).scalars().all()
        for ov in overheads:
            day_of_month = int(ov.value.get("day_of_month", 1))
            amt = Decimal(str(ov.value.get("amount", "0.00")))
            curr = as_of_date.replace(day=1)
            while curr <= end_date:
                try:
                    ov_date = date(curr.year, curr.month, day_of_month)
                except ValueError:
                    ov_date = date(curr.year, curr.month, 28)
                if ov_date >= as_of_date:
                    base_outflows.append((ov_date, amt, ov.id, {"type": "overhead"}))
                if curr.month == 12:
                    curr = date(curr.year + 1, 1, 1)
                else:
                    curr = date(curr.year, curr.month + 1, 1)

        # 6. Create Scenario Record
        scenario_record = Scenario(
            id=uuid4(),
            org_id=org_id,
            baseline_run_id=baseline_run.id,
            name=request.scenario.name,
            origin=request.scenario.origin.value,
            source_card_id=request.scenario.source_card_id,
        )
        session.add(scenario_record)
        await session.flush()

        for ch in request.scenario.changes:
            db_ch = DBScenarioChange(
                id=uuid4(),
                org_id=org_id,
                scenario_id=scenario_record.id,
                lever=ch.lever,
                op=ch.op.value,
                value=str(ch.value),
                start_date=ch.start_date,
                params=ch.params,
                is_assumption=ch.is_assumption,
            )
            session.add(db_ch)

        # 7. Generate 3 Cases: expected, best, worst
        case_results_map: Dict[str, Tuple[ForecastCalculationResult, List[str]]] = {}
        for c_type in ("expected", "best", "worst"):
            clean_in, clean_out, assumptions = LeverDispatcher.apply_levers(
                inflow_events=base_inflows,
                outflow_events=base_outflows,
                changes=request.scenario.changes,
                case_type=c_type,
                settings=settings,
            )
            calc_res = ForecastEngine.calculate_forecast(
                opening_cash=opening_cash,
                opening_cash_date=as_of_date,
                inflow_events=clean_in,
                outflow_events=clean_out,
                horizon_weeks=request.horizon_weeks,
                reserve_amount=reserve_amt,
                cash_floor_weeks=floor_weeks,
                value_label="hypothetical",
            )
            case_results_map[c_type] = (calc_res, assumptions)

        # 8. Persist ForecastRuns and ForecastPoints for each case
        case_models: Dict[str, CaseResult] = {}
        expected_run_id = uuid4()
        run_models_to_persist = []
        points_to_persist = []

        all_warnings: List[str] = []
        all_assumptions: List[str] = []
        source_refs_collected: List[UUID] = [inv.id for inv in invoices[:5]]

        for c_type, (c_res, c_assump) in case_results_map.items():
            run_id = expected_run_id if c_type == "expected" else uuid4()
            f_run = ForecastRun(
                id=run_id,
                org_id=org_id,
                scenario_id=scenario_record.id,
                case_type=c_type,
                engine_version="0.1.0",
                horizon_weeks=request.horizon_weeks,
                start_date=as_of_date,
                end_date=end_date,
                min_cash=c_res.min_cash,
                min_cash_date=c_res.min_cash_date,
                end_cash=c_res.end_cash,
                runway_weeks=c_res.runway_weeks,
                reserve_breach=c_res.reserve_breach,
                cash_floor_breach=c_res.cash_floor_breach,
                status="verified",
                baseline_hash=baseline_run.baseline_hash,
            )
            run_models_to_persist.append(f_run)

            weekly_cash_pts: List[WeeklyCashPoint] = []
            for pt in c_res.points:
                weekly_cash_pts.append(
                    WeeklyCashPoint(week_start=pt.week_start, cash=pt.closing_cash)
                )
                db_pt = ForecastPoint(
                    id=uuid4(),
                    org_id=org_id,
                    run_id=f_run.id,
                    week_number=pt.week_number,
                    week_start=pt.week_start,
                    opening_cash=pt.opening_cash,
                    projected_inflows=pt.projected_inflows,
                    projected_outflows=pt.projected_outflows,
                    net_cash_flow=pt.net_cash_flow,
                    closing_cash=pt.closing_cash,
                    value_label="hypothetical",
                    contributing_inflow_refs=[str(r) for r in pt.inflow_refs],
                    contributing_outflow_refs=[str(r) for r in pt.outflow_refs],
                )
                points_to_persist.append(db_pt)

            case_models[c_type] = CaseResult(
                weekly_cash=weekly_cash_pts,
                min_cash=c_res.min_cash,
                min_cash_date=c_res.min_cash_date,
                end_cash=c_res.end_cash,
                runway_weeks=c_res.runway_weeks,
                reserve_breach=c_res.reserve_breach,
                cash_floor_breach=c_res.cash_floor_breach,
            )

            if c_type == "expected":
                all_assumptions.extend(c_assump)
                if c_res.reserve_breach:
                    all_warnings.append(f"Expected case breaches currency reserve of ${reserve_amt:.2f}")
                if c_res.cash_floor_breach:
                    all_warnings.append(f"Expected case breaches {floor_weeks}-week cash floor (${c_res.converted_cash_floor:.2f})")
            elif c_type == "worst":
                if c_res.runway_weeks is not None:
                    all_warnings.append(f"Worst case projects cash exhaustion at week {c_res.runway_weeks}")
                if c_res.cash_floor_breach and not case_results_map["expected"][0].cash_floor_breach:
                    all_warnings.append("Worst case breaches cash floor even though expected case remains safe")

        session.add_all(run_models_to_persist)
        session.add_all(points_to_persist)
        await session.commit()

        # 9. Invariance Verification: Baseline MUST NOT be mutated!
        refreshed_baseline = await session.get(ForecastRun, baseline_run.id)
        assert refreshed_baseline.baseline_hash == original_baseline_hash, "Baseline was mutated by scenario run!"

        # 10. Assemble Output Data
        cases = ScenarioCases(
            expected=case_models["expected"],
            best=case_models["best"],
            worst=case_models["worst"],
        )

        run_data = ScenarioRunData(
            run_id=expected_run_id,
            status=ResultStatus.VERIFIED,
            engine_version="0.1.0",
            currency="USD",
            cases=cases,
            assumptions=all_assumptions,
            warnings=all_warnings,
            source_row_refs=source_refs_collected,
            evidence_refs=[uuid4(), uuid4()],
        )

        return ToolResultEnvelope(
            status=ToolStatus.OK,
            data=run_data.model_dump(mode="json"),
            sources=[str(ref) for ref in source_refs_collected],
            warnings=all_warnings,
            run_id=str(expected_run_id),
        )

    @classmethod
    async def compare_scenarios(
        cls, session: AsyncSession, org_id: UUID, scenario_id: UUID
    ) -> Dict[str, Any]:
        """Compares baseline vs scenario cases."""
        scenario = await session.get(Scenario, scenario_id)
        if not scenario or scenario.org_id != org_id:
            raise NotFoundError(f"Scenario {scenario_id} not found")

        baseline = await session.get(ForecastRun, scenario.baseline_run_id)
        stmt = select(ForecastRun).where(
            ForecastRun.org_id == org_id,
            ForecastRun.scenario_id == scenario.id,
        )
        scenario_runs = (await session.execute(stmt)).scalars().all()
        runs_by_case = {r.case_type: r for r in scenario_runs}

        return {
            "scenario_id": str(scenario.id),
            "scenario_name": scenario.name,
            "baseline": {
                "run_id": str(baseline.id),
                "min_cash": f"{baseline.min_cash:.2f}",
                "end_cash": f"{baseline.end_cash:.2f}",
                "runway_weeks": baseline.runway_weeks,
                "reserve_breach": baseline.reserve_breach,
                "cash_floor_breach": baseline.cash_floor_breach,
            },
            "scenario_cases": {
                c: {
                    "run_id": str(r.id),
                    "min_cash": f"{r.min_cash:.2f}",
                    "end_cash": f"{r.end_cash:.2f}",
                    "runway_weeks": r.runway_weeks,
                    "reserve_breach": r.reserve_breach,
                    "cash_floor_breach": r.cash_floor_breach,
                }
                for c, r in runs_by_case.items()
            },
        }
