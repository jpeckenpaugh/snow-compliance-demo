#!/usr/bin/env python3
"""Transparent, rule-based contract-risk rubric shared by the POC.

This is the single source of truth for the simulated rubric and mirrors the
data-driven rules in ``sql/04_risk_views.sql`` (``CORE.ref_risk_rule``). The
banding is identical: High >= 60, Medium 30-59, Low < 30.

Rule signals use CUAD v1's ACTUAL clause categories (verified in
``poc/analysis/cuad_shape_report.md``); CUAD has no "Indemnification" or
"Limitation of Liability" category -- liability exposure is expressed as
"Uncapped Liability" / "Cap On Liability".

This rubric is a demonstration of analytics mechanics, not legal advice.
"""

# (driver label, points, signal, categories)
#   signal "present" -> points when at least one category is present
#   signal "absent"  -> points when none of the categories are present
RULES = [
    ("Uncapped liability", 40, "present", ["Uncapped Liability"]),
    ("No cap on liability", 20, "absent", ["Cap On Liability"]),
    ("Termination for convenience", 15, "present", ["Termination For Convenience"]),
    ("Anti-assignment", 10, "present", ["Anti-Assignment"]),
    ("Change of control", 10, "present", ["Change Of Control"]),
    ("Minimum commitment", 10, "present", ["Minimum Commitment"]),
    ("No governing law", 10, "absent", ["Governing Law"]),
    ("Restrictive covenant", 5, "present", ["Non-Compete", "Exclusivity"]),
]


def band(score):
    return "High" if score >= 60 else "Medium" if score >= 30 else "Low"


def score_contract(present_categories):
    """Score one contract.

    ``present_categories`` is any iterable of clause-category names that are
    present in the document. Returns ``(score, band, drivers)``.
    """
    present = set(present_categories)
    score = 0
    drivers = []
    for label, points, signal, categories in RULES:
        hit = any(c in present for c in categories)
        if (signal == "present" and hit) or (signal == "absent" and not hit):
            score += points
            drivers.append(label)
    return score, band(score), drivers


def register_rows(present_by_contract):
    """Build risk-register rows for many contracts.

    ``present_by_contract`` maps contract_id -> iterable of present categories.
    Returns a list of dicts ordered by descending score.
    """
    rows = []
    for contract_id, present_categories in present_by_contract.items():
        score, risk_band, drivers = score_contract(present_categories)
        rows.append({
            "contract_id": contract_id,
            "risk_score": score,
            "risk_band": risk_band,
            "risk_drivers": drivers,
        })
    rows.sort(key=lambda r: (-r["risk_score"], r["contract_id"]))
    return rows
