from copy import deepcopy
from datetime import date, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from packages.contracts.finance import ScenarioChange


class LeverDispatcher:
    """Dispatches and applies MVP levers as deltas over an in-memory schedule.

    Historical transactions and base records are never mutated.
    """

    SUPPORTED_LEVERS = {
        "hire",
        "payment_delay",
        "payment_terms_days",
        "deposit_pct",
        "revenue_change_pct",
        "lost_client",
        "price_change_pct",
        "expense_change",
    }

    @classmethod
    def apply_levers(
        cls,
        inflow_events: List[Tuple[date, Decimal, UUID, Dict[str, Any]]],
        outflow_events: List[Tuple[date, Decimal, UUID, Dict[str, Any]]],
        changes: List[ScenarioChange],
        case_type: str = "expected",
        settings: Optional[Any] = None,
    ) -> Tuple[List[Tuple[date, Decimal, UUID]], List[Tuple[date, Decimal, UUID]], List[str]]:
        # Deepcopy to ensure pure deltas
        modified_inflows = [
            (d, amt, ref, deepcopy(meta)) for d, amt, ref, meta in inflow_events
        ]
        modified_outflows = [
            (d, amt, ref, deepcopy(meta)) for d, amt, ref, meta in outflow_events
        ]
        assumptions_applied: List[str] = []

        # Case-specific offsets
        worst_delay_days = getattr(settings, "worst_case_delay_days", 14) if settings else 14
        best_advance_days = getattr(settings, "best_case_advance_days", 7) if settings else 7
        worst_rev_delta = getattr(settings, "worst_case_rev_pct_delta", Decimal("-10.00")) if settings else Decimal("-10.00")
        best_rev_delta = getattr(settings, "best_case_rev_pct_delta", Decimal("5.00")) if settings else Decimal("5.00")

        # 1. Apply Case Adjustments to Uncertain Inflows
        if case_type == "worst":
            assumptions_applied.append(f"Worst case: uncertain client payments delayed by +{worst_delay_days} days")
            adjusted_inflows = []
            for d, amt, ref, meta in modified_inflows:
                if meta.get("is_uncertain", False):
                    adjusted_inflows.append((d + timedelta(days=worst_delay_days), amt, ref, meta))
                else:
                    adjusted_inflows.append((d, amt, ref, meta))
            modified_inflows = adjusted_inflows
        elif case_type == "best":
            assumptions_applied.append(f"Best case: uncertain client payments accelerated by -{best_advance_days} days")
            adjusted_inflows = []
            for d, amt, ref, meta in modified_inflows:
                if meta.get("is_uncertain", False):
                    adjusted_inflows.append((d - timedelta(days=best_advance_days), amt, ref, meta))
                else:
                    adjusted_inflows.append((d, amt, ref, meta))
            modified_inflows = adjusted_inflows

        # 2. Apply Explicit Scenario Changes
        for change in changes:
            lever = change.lever.lower().strip()
            if lever not in cls.SUPPORTED_LEVERS:
                raise ValueError(f"Unsupported lever: {lever}")

            if lever == "hire":
                # params: count, monthly_cost, start_date
                count = int(change.params.get("count", change.value))
                raw_cost = change.params.get("monthly_cost", "7000.00")
                monthly_cost = Decimal(str(raw_cost))
                start_d = change.start_date or date(2026, 11, 1)

                # Inject weekly recurring outflow for each hire
                weekly_salary = (monthly_cost * Decimal("12.00")) / Decimal("52.00")
                total_weekly_cost = weekly_salary * Decimal(str(count))

                # Inject for 52 forward weeks from start_date
                for w in range(52):
                    event_date = start_d + timedelta(weeks=w)
                    meta = {"type": "scenario_hire", "count": count, "monthly_cost": str(monthly_cost)}
                    modified_outflows.append((event_date, total_weekly_cost, change.params.get("source_card_id") or UUID(int=0), meta))

                assumptions_applied.append(f"Hired {count} staff starting {start_d} at ${monthly_cost:.2f}/mo each")

            elif lever == "payment_delay":
                # params: client or invoice, days
                days = int(change.params.get("days", change.value))
                client_target = change.params.get("client")
                invoice_target = change.params.get("invoice")

                delayed_inflows = []
                for d, amt, ref, meta in modified_inflows:
                    matches_client = client_target and meta.get("client") == client_target
                    matches_inv = invoice_target and meta.get("invoice_number") == invoice_target
                    if matches_client or matches_inv:
                        delayed_inflows.append((d + timedelta(days=days), amt, ref, meta))
                    else:
                        delayed_inflows.append((d, amt, ref, meta))
                modified_inflows = delayed_inflows
                target_desc = f"client {client_target}" if client_target else f"invoice {invoice_target}"
                assumptions_applied.append(f"Payment for {target_desc} delayed by {days} days")

            elif lever == "revenue_change_pct":
                pct = Decimal(str(change.value))
                if case_type == "worst":
                    pct += Decimal(str(worst_rev_delta))
                elif case_type == "best":
                    pct += Decimal(str(best_rev_delta))

                start_d = change.start_date or date(2026, 11, 1)
                multiplier = Decimal("1.00") + (pct / Decimal("100.00"))

                scaled_inflows = []
                for d, amt, ref, meta in modified_inflows:
                    if d >= start_d:
                        scaled_inflows.append((d, amt * multiplier, ref, meta))
                    else:
                        scaled_inflows.append((d, amt, ref, meta))
                modified_inflows = scaled_inflows
                assumptions_applied.append(f"Revenue changed by {pct:.2f}% starting {start_d}")

            elif lever == "lost_client":
                client = change.params.get("client", str(change.value))
                cut_date = change.start_date or date(2026, 11, 1)

                filtered_inflows = []
                for d, amt, ref, meta in modified_inflows:
                    if meta.get("client") == client and d >= cut_date:
                        continue  # Inflow zeroed out
                    filtered_inflows.append((d, amt, ref, meta))
                modified_inflows = filtered_inflows
                assumptions_applied.append(f"Lost client {client} effective {cut_date}")

            elif lever == "expense_change":
                amt = Decimal(str(change.value))
                cadence = change.params.get("cadence", "monthly")
                start_d = change.start_date or date(2026, 11, 1)

                if cadence == "monthly":
                    weekly_amt = (amt * Decimal("12.00")) / Decimal("52.00")
                    for w in range(52):
                        modified_outflows.append((start_d + timedelta(weeks=w), weekly_amt, UUID(int=0), {"type": "expense_change"}))
                else:  # one-off
                    modified_outflows.append((start_d, amt, UUID(int=0), {"type": "expense_change"}))
                assumptions_applied.append(f"Expense changed by ${amt:.2f} ({cadence}) starting {start_d}")

            elif lever == "payment_terms_days":
                days = int(change.value)
                start_d = change.start_date or date(2026, 11, 1)
                shifted = []
                for d, amt, ref, meta in modified_inflows:
                    if d >= start_d:
                        shifted.append((d + timedelta(days=days), amt, ref, meta))
                    else:
                        shifted.append((d, amt, ref, meta))
                modified_inflows = shifted
                assumptions_applied.append(f"Payment terms shifted by {days} days from {start_d}")

            elif lever == "deposit_pct":
                pct = Decimal(str(change.value)) / Decimal("100.00")
                start_d = change.start_date or date(2026, 11, 1)
                split_inflows = []
                for d, amt, ref, meta in modified_inflows:
                    if d >= start_d:
                        # Deposit collected immediately at start_d, remainder at original d
                        deposit_amt = amt * pct
                        remainder_amt = amt - deposit_amt
                        split_inflows.append((start_d, deposit_amt, ref, meta))
                        split_inflows.append((d, remainder_amt, ref, meta))
                    else:
                        split_inflows.append((d, amt, ref, meta))
                modified_inflows = split_inflows
                assumptions_applied.append(f"Deposit terms: {change.value}% upfront from {start_d}")

            elif lever == "price_change_pct":
                pct = Decimal(str(change.value))
                start_d = change.start_date or date(2026, 11, 1)
                mult = Decimal("1.00") + (pct / Decimal("100.00"))
                re为其 = []
                for d, amt, ref, meta in modified_inflows:
                    if d >= start_d:
                        re为其.append((d, amt * mult, ref, meta))
                    else:
                        re为其.append((d, amt, ref, meta))
                modified_inflows = re为其
                assumptions_applied.append(f"Price adjusted by {pct:.2f}% starting {start_d}")

        # Strip metadata back to standard 3-tuples for engine
        clean_inflows = [(d, amt, ref) for d, amt, ref, _ in modified_inflows]
        clean_outflows = [(d, amt, ref) for d, amt, ref, _ in modified_outflows]

        return clean_inflows, clean_outflows, assumptions_applied
