from typing import Any, Dict, List, Optional, Tuple


class ColumnMapper:
    """Detects column mappings and identifies ambiguous headers requiring user resolution."""

    CANDIDATE_PATTERNS = {
        "invoice_number": ["invoice_number", "invoice_no", "inv_num", "inv_no", "invoice_id", "number"],
        "client_or_vendor": ["client", "vendor", "customer", "client_or_vendor", "client_name", "account"],
        "amount": ["amount", "total", "invoice_amount", "gross_amount", "net_amount", "value"],
        "issue_date": ["issue_date", "invoice_date", "issued_on", "bill_date", "date"],
        "due_date": ["due_date", "payment_due", "due_on", "expected_due"],
        "expected_payment_date": ["expected_payment_date", "expected_date", "payment_expected", "projected_payment_date"],
        "status": ["status", "payment_status", "state", "invoice_status"],
    }

    @classmethod
    def analyze_headers(
        cls, headers: List[str], file_type: str = "invoices"
    ) -> Tuple[Dict[str, str], List[Dict[str, Any]]]:
        normalized = {h.strip().lower().replace(" ", "_"): h for h in headers}
        mapping: Dict[str, str] = {}
        ambiguities: List[Dict[str, Any]] = []

        # Check for ambiguity: e.g. both 'date' and 'due_date' present, or both 'amount' and 'total'
        date_candidates = [raw for norm, raw in normalized.items() if "date" in norm]
        if len(date_candidates) > 1 and "due_date" not in normalized and "issue_date" not in normalized:
            ambiguities.append({
                "field": "issue_date_vs_due_date",
                "description": "Multiple ambiguous date columns detected without explicit issue or due date label",
                "candidates": date_candidates,
            })

        amount_candidates = [raw for norm, raw in normalized.items() if norm in ("amount", "total", "gross", "net")]
        if len(amount_candidates) > 1 and "amount" in normalized and "total" in normalized:
            ambiguities.append({
                "field": "amount_vs_total",
                "description": "Both 'amount' and 'total' headers found. Please specify which represents the receivable total.",
                "candidates": amount_candidates,
            })

        # Build default mapping from recognized candidates
        for canonical_field, patterns in cls.CANDIDATE_PATTERNS.items():
            for p in patterns:
                if p in normalized:
                    mapping[canonical_field] = normalized[p]
                    break

        return mapping, ambiguities
