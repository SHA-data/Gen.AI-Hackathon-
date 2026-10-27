from decimal import Decimal
from typing import List, Optional, Tuple

from packages.contracts.envelope import ResultStatus
from services.api.app.cfo.models import ForecastPoint, ForecastRun


class FinanceVerifier:
    """Rigorous verification engine enforcing V1, V4, and V5 integrity rules."""

    @classmethod
    def verify_run(
        cls,
        run: ForecastRun,
        points: List[ForecastPoint],
        baseline_run: Optional[ForecastRun] = None,
        expected_currency: str = "USD",
    ) -> Tuple[ResultStatus, List[str]]:
        warnings: List[str] = []

        if not points:
            return ResultStatus.FAILED, ["Verification failed: Forecast points list is empty."]

        # --- V5: Units, Currency, Sign, and Date Consistency ---
        if len(expected_currency) != 3:
            return ResultStatus.FAILED, [f"V5 Failed: Invalid currency format '{expected_currency}'"]

        for idx, pt in enumerate(points):
            expected_net = pt.projected_inflows - pt.projected_outflows
            if pt.net_cash_flow != expected_net:
                return ResultStatus.FAILED, [
                    f"V5 Failed: Point week {pt.week_number} net cash flow {pt.net_cash_flow} "
                    f"does not match inflows ({pt.projected_inflows}) - outflows ({pt.projected_outflows})"
                ]

            if idx > 0:
                prev_pt = points[idx - 1]
                # Week-to-week opening cash continuity
                if pt.opening_cash != prev_pt.closing_cash:
                    return ResultStatus.FAILED, [
                        f"V1/V5 Failed: Week {pt.week_number} opening cash ({pt.opening_cash}) "
                        f"does not match week {prev_pt.week_number} closing cash ({prev_pt.closing_cash})"
                    ]
                # Weekly sequential check (7 days apart)
                if (pt.week_start - prev_pt.week_start).days != 7:
                    return ResultStatus.FAILED, [
                        f"V5 Failed: Date continuity broken between week {prev_pt.week_number} "
                        f"({prev_pt.week_start}) and week {pt.week_number} ({pt.week_start})"
                    ]

        # --- V1: Numbers Check (Recomputation from Stored Points) ---
        calculated_min = min(p.closing_cash for p in points)
        if run.min_cash != calculated_min:
            return ResultStatus.FAILED, [
                f"V1 Failed: Stored min_cash ({run.min_cash}) does not match points minimum ({calculated_min})"
            ]

        calculated_end = points[-1].closing_cash
        if run.end_cash != calculated_end:
            return ResultStatus.FAILED, [
                f"V1 Failed: Stored end_cash ({run.end_cash}) does not match final point ({calculated_end})"
            ]

        # --- V4: Scenarios Check (Same baseline invariant) ---
        if run.case_type != "baseline":
            if not baseline_run:
                return ResultStatus.FAILED, ["V4 Failed: Scenario run has no associated baseline run"]
            if run.baseline_hash != baseline_run.baseline_hash:
                return ResultStatus.FAILED, [
                    f"V4 Failed: Scenario baseline hash ({run.baseline_hash}) "
                    f"diverged from baseline ({baseline_run.baseline_hash})"
                ]

        # Breaches generate warnings rather than hard failures
        if run.reserve_breach:
            warnings.append("Warning: Forecast breaches tenant currency reserve")
        if run.cash_floor_breach:
            warnings.append("Warning: Forecast breaches weeks-converted cash floor")

        status = ResultStatus.WARNING if warnings else ResultStatus.VERIFIED
        return status, warnings
