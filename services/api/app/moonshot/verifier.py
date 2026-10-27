"""Strict Claim & Quote Verification Engine (PDF Section 12; Card 5 Stage 8).

Implements hard rules HR-01, HR-02, HR-04, HR-07, and HR-08:
- HR-01: Claim tags (cited, computed, inferred, commentary).
- HR-04: Excerpt length <= 300 chars; exact quote SHA-256 hash check.
- HR-02/HR-07: Every computed figure must appear in a referenced scenario run.
- HR-08: Mandatory disclaimer check.
"""
from __future__ import annotations

import hashlib
import re
from typing import Any, Dict, List, Literal, Optional, Tuple
from packages.contracts.finance import ScenarioRunResponse

ALLOWED_CLAIM_TAGS = {"cited", "computed", "inferred", "commentary"}
MANDATORY_DISCLAIMER_PHRASE = "decision support, not financial advice"


def compute_sha256(text: str) -> str:
    """Compute normalized SHA-256 hash for quote verification."""
    clean = " ".join(text.strip().split())
    return hashlib.sha256(clean.encode("utf-8")).hexdigest()


def verify_quote(quote: str, stored_hash: str) -> Tuple[bool, Optional[str]]:
    """Verify that a quote does not exceed 300 chars and matches its stored SHA-256 hash."""
    if len(quote) > 300:
        return False, f"Quote exceeds maximum allowed 300 characters (length: {len(quote)})"

    actual_hash = compute_sha256(quote)
    if actual_hash != stored_hash.lower():
        return False, f"Quote hash mismatch. Expected {stored_hash}, got {actual_hash}"

    return True, None


def verify_computed_amount(amount: float, scenario_response: ScenarioRunResponse) -> Tuple[bool, Optional[str]]:
    """Verify that a cash amount stated in a claim exists in the referenced scenario run."""
    # Check expected, best, and worst case numbers
    tolerated_delta = 1.0  # $1 rounding tolerance
    all_cash_values = []

    for case in [scenario_response.cases.expected, scenario_response.cases.best, scenario_response.cases.worst]:
        all_cash_values.append(float(case.end_cash))
        all_cash_values.append(float(case.min_cash))
        for pt in case.weekly_cash:
            all_cash_values.append(float(pt.cash))

    matched = any(abs(amount - val) <= tolerated_delta for val in all_cash_values)
    if not matched:
        return False, f"Amount ${amount:,.2f} could not be verified against scenario run {scenario_response.run_id}"

    return True, None


def verify_disclaimer_presence(text: str) -> bool:
    """Verify that the mandatory disclaimer is explicitly present in prose or report export."""
    return MANDATORY_DISCLAIMER_PHRASE in text.lower()


def audit_claim(
    claim_text: str,
    tag: Literal["cited", "computed", "inferred", "commentary"],
    quote_ref: Optional[Tuple[str, str]] = None,  # (quote_text, stored_hash)
    scenario_ref: Optional[Tuple[float, ScenarioRunResponse]] = None,  # (amount, scenario_response)
) -> Dict[str, Any]:
    """Audit a single claim and assign status: verified | warning | unverified | failed."""
    if tag not in ALLOWED_CLAIM_TAGS:
        return {
            "claim": claim_text,
            "tag": tag,
            "status": "failed",
            "reason": f"Invalid claim tag '{tag}'",
        }

    if tag == "cited":
        if not quote_ref:
            return {
                "claim": claim_text,
                "tag": tag,
                "status": "unverified",
                "reason": "Cited claim missing quote reference and excerpt hash",
            }
        valid, err = verify_quote(quote_ref[0], quote_ref[1])
        if not valid:
            return {"claim": claim_text, "tag": tag, "status": "failed", "reason": err}
        return {"claim": claim_text, "tag": tag, "status": "verified"}

    elif tag == "computed":
        if not scenario_ref:
            return {
                "claim": claim_text,
                "tag": tag,
                "status": "unverified",
                "reason": "Computed claim missing scenario run reference",
            }
        valid, err = verify_computed_amount(scenario_ref[0], scenario_ref[1])
        if not valid:
            return {"claim": claim_text, "tag": tag, "status": "unverified", "reason": err}
        return {"claim": claim_text, "tag": tag, "status": "verified"}

    # Inferred and commentary are valid when visibly marked
    return {"claim": claim_text, "tag": tag, "status": "verified"}
