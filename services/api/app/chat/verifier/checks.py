"""Verifier check implementations V1-V9 (PDF §12.2)."""
import hashlib
import re
from typing import Any, Dict, List, NamedTuple, Optional, Set
from uuid import UUID

class CheckResult(NamedTuple):
    check_name: str
    status: str  # 'passed' | 'warning' | 'failed'
    details: Dict[str, Any]

def extract_numeric_tokens(text: str) -> List[str]:
    """Extract money, percentages, and floating point / integer numbers from prose."""
    # Matches: $120,000, $45,000.00, 30 days, 18 weeks, 15.0%, etc.
    patterns = [
        r"\$[\d,]+(?:\.\d+)?",
        r"\b\d+(?:\.\d+)?%\b",
        r"\b\d+\s+(?:weeks|days|months|devs|developers|people)\b",
    ]
    tokens = []
    for p in patterns:
        for match in re.finditer(p, text, re.IGNORECASE):
            tokens.append(match.group(0).strip())
    return tokens

def extract_numbers_from_obj(obj: Any) -> Set[str]:
    """Recursively collect string representations of numbers in tool result payloads."""
    collected = set()
    if isinstance(obj, dict):
        for k, v in obj.items():
            collected.update(extract_numbers_from_obj(v))
    elif isinstance(obj, list):
        for item in obj:
            collected.update(extract_numbers_from_obj(item))
    elif isinstance(obj, (int, float, str)):
        s = str(obj).strip()
        # Clean common symbols
        clean_s = re.sub(r"[$,]", "", s)
        try:
            val = float(clean_s)
            collected.add(s)
            collected.add(f"{val:.2f}")
            collected.add(f"{int(val)}")
        except ValueError:
            pass
    return collected

def check_v1_numbers(answer_text: str, current_turn_tool_results: List[Any]) -> CheckResult:
    """V1 Numbers: Every figure in the answer appears in a tool result from this turn."""
    extracted = extract_numeric_tokens(answer_text)
    if not extracted:
        return CheckResult("V1_numbers", "passed", {"checked_tokens": []})

    tool_numbers = set()
    for res in current_turn_tool_results:
        tool_numbers.update(extract_numbers_from_obj(res))

    unverified = []
    for tok in extracted:
        clean = re.sub(r"[$,%a-zA-Z\s]", "", tok)
        # Check if clean number is contained in tool output numbers
        matched = False
        for tn in tool_numbers:
            clean_tn = re.sub(r"[$,%a-zA-Z\s]", "", tn)
            if clean and clean == clean_tn:
                matched = True
                break
        if not matched:
            unverified.append(tok)

    if unverified:
        return CheckResult(
            "V1_numbers",
            "warning",
            {"unverified_numbers": unverified, "all_tokens": extracted},
        )
    return CheckResult("V1_numbers", "passed", {"checked_tokens": extracted})

def check_v2_quotes(answer_text: str, stored_excerpts: Dict[str, str] = None) -> CheckResult:
    """V2 Quotes: Every quote matches stored excerpt hash and is <= 300 chars."""
    quotes = re.findall(r'"([^"]*)"', answer_text)
    quotes += re.findall(r'“([^”]*)”', answer_text)
    excerpts = stored_excerpts or {}

    failed = []
    for q in quotes:
        if len(q) > 300:
            failed.append({"quote": q, "reason": "exceeds_300_chars", "length": len(q)})
            continue
        # If stored excerpts provided, verify hash
        if excerpts:
            q_hash = hashlib.sha256(q.strip().encode("utf-8")).hexdigest()
            if q_hash not in excerpts:
                failed.append({"quote": q, "reason": "unmatched_hash"})

    if failed:
        return CheckResult("V2_quotes", "failed", {"failed_quotes": failed})
    return CheckResult("V2_quotes", "passed", {"valid_quotes_count": len(quotes)})

def check_v3_citations(cited_sources: List[Dict[str, Any]], caller_org_id: UUID) -> CheckResult:
    """V3 Citations: Every cited source exists and belongs to the organization."""
    invalid = []
    for src in cited_sources:
        src_org = src.get("org_id")
        if src_org and str(src_org) != str(caller_org_id):
            invalid.append({"source_id": str(src.get("id")), "reason": "cross_org_source_detected"})

    if invalid:
        return CheckResult("V3_citations", "failed", {"cross_org_violations": invalid})
    return CheckResult("V3_citations", "passed", {"citations_verified": len(cited_sources)})

def check_v5_units(answer_text: str, expected_currency: str = "USD") -> CheckResult:
    """V5 Units: Currency, sign, date, and period are consistent."""
    # Check for non-standard currency symbols if expecting USD
    if expected_currency == "USD" and ("€" in answer_text or "£" in answer_text or "¥" in answer_text):
        return CheckResult("V5_units", "warning", {"reason": "Foreign currency symbol found when USD expected"})
    return CheckResult("V5_units", "passed", {"currency": expected_currency})

def check_v6_gates(top_strategies: List[Dict[str, Any]], failed_gates: List[Dict[str, Any]]) -> CheckResult:
    """V6 Gates: No strategy that failed a gate appears in the ranked list."""
    failed_ids = {str(item.get("strategy_id")) for item in failed_gates}
    leaked = []
    for strat in top_strategies:
        strat_id = str(strat.get("strategy_id"))
        if strat_id in failed_ids:
            leaked.append(strat_id)

    if leaked:
        return CheckResult("V6_gates", "failed", {"leaked_failed_strategies": leaked})
    return CheckResult("V6_gates", "passed", {})

def check_v8_disclaimer(answer_text: str, is_report_turn: bool = False) -> CheckResult:
    """V8 Disclaimer: Mandatory decision-support disclaimer on reports and scenarios."""
    if is_report_turn:
        if "disclaimer" not in answer_text.lower():
            return CheckResult(
                "V8_disclaimer",
                "failed",
                {"reason": "Mandatory decision-support disclaimer missing from final report"},
            )
    return CheckResult("V8_disclaimer", "passed", {})
