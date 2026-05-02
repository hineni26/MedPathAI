import random
import json
from datetime import datetime


# ── PFL credit policy ──────────────────────────────────────────────────────────
PFL_POLICY = {
    "lender":          "Poonawalla Fincorp",
    "min_cibil":       700,
    "warn_cibil":      650,       # yellow zone
    "max_foir":        0.50,
    "warn_foir":       0.55,      # yellow zone
    "min_income":      15_000,
    "max_loan":        3_000_000,
    "base_rate":       9.99,
    "processing_fee":  0.01,      # 1%
    "max_tenure":      48,
}


# ── EMI calculator ─────────────────────────────────────────────────────────────

def calc_emi(principal: float, months: int, annual_rate: float) -> int:
    """Standard reducing-balance EMI formula."""
    if months <= 0 or annual_rate <= 0:
        return int(principal / max(months, 1))
    r = (annual_rate / 100) / 12
    emi = principal * r * (1 + r) ** months / ((1 + r) ** months - 1)
    return int(round(emi))


# ── Best tenure finder ─────────────────────────────────────────────────────────

def find_best_tenure(loan_amount: float, monthly_income: float,
                     existing_emi: float, rate: float) -> dict | None:
    """
    Find the shortest tenure that keeps FOIR under PFL's 50% limit.
    Returns dict with tenure_months, emi, foir — or None if impossible.
    """
    for months in [12, 24, 36, 48]:
        proposed_emi = calc_emi(loan_amount, months, rate)
        total_emi    = existing_emi + proposed_emi
        foir         = total_emi / monthly_income if monthly_income else 1.0
        if foir <= PFL_POLICY["max_foir"]:
            return {
                "tenure_months":  months,
                "emi":            proposed_emi,
                "foir":           round(foir, 4),
                "total_emi":      int(total_emi),
            }
    return None


# ── Core eligibility engine ────────────────────────────────────────────────────

def run_eligibility(
    loan_amount:      float,
    monthly_income:   float,
    existing_emi:     float,
    cibil_score:      int,
    employment_years: float,
    age:              int = 35,
) -> dict:
    """
    Runs PFL pre-qualification checks.

    Returns a result dict with:
        decision:   GREEN / YELLOW / RED
        risk_band:  A / B / C / D
        checks:     per-check pass/warn/fail details
        flags:      list of hard/soft flag codes
        offer:      recommended loan terms (if not RED)
        alternatives: list of alternatives (if RED)
    """
    flags  = []
    checks = {}

    # ── Check 1: CIBIL ────────────────────────────────────────────────────────
    if cibil_score >= 750:
        checks["cibil"] = {"status": "PASS", "label": "Excellent credit score ✅", "value": cibil_score}
    elif cibil_score >= PFL_POLICY["min_cibil"]:
        checks["cibil"] = {"status": "PASS", "label": "Good credit score ✅",      "value": cibil_score}
    elif cibil_score >= PFL_POLICY["warn_cibil"]:
        checks["cibil"] = {"status": "WARN", "label": "Fair — higher rate may apply ⚠️", "value": cibil_score}
        flags.append("LOW_CIBIL")
    else:
        checks["cibil"] = {"status": "FAIL", "label": "Below PFL minimum (700) ❌", "value": cibil_score}
        flags.append("CIBIL_REJECTED")

    # ── Check 2: Income ───────────────────────────────────────────────────────
    if monthly_income >= PFL_POLICY["min_income"]:
        checks["income"] = {"status": "PASS", "label": f"Income ₹{monthly_income:,.0f}/month ✅"}
    else:
        checks["income"] = {"status": "FAIL", "label": f"Below PFL minimum ₹15,000/month ❌"}
        flags.append("INCOME_TOO_LOW")

    # ── Check 3: Loan-to-income multiple ──────────────────────────────────────
    max_eligible = monthly_income * 10
    if loan_amount <= max_eligible:
        checks["income_multiple"] = {"status": "PASS", "label": "Loan within 10× monthly income ✅"}
    else:
        checks["income_multiple"] = {"status": "FAIL",
            "label": f"Loan exceeds 10× income (max eligible ₹{max_eligible:,.0f}) ❌"}
        flags.append("INCOME_TOO_LOW")

    # ── Check 4: FOIR — find best tenure ─────────────────────────────────────
    rate         = PFL_POLICY["base_rate"]
    tenure_data  = find_best_tenure(loan_amount, monthly_income, existing_emi, rate)

    if tenure_data:
        foir = tenure_data["foir"]
        checks["foir"] = {
            "status": "PASS",
            "label":  f"FOIR {round(foir*100)}% — within PFL limit (50%) ✅",
            "value":  foir,
        }
    else:
        # Even at 48 months FOIR exceeds 50% — check yellow zone
        proposed_emi_48 = calc_emi(loan_amount, 48, rate)
        foir_48 = (existing_emi + proposed_emi_48) / monthly_income if monthly_income else 1.0
        checks["foir"] = {
            "status": "FAIL" if foir_48 > PFL_POLICY["warn_foir"] else "WARN",
            "label":  f"FOIR {round(foir_48*100)}% — exceeds PFL limit ❌",
            "value":  foir_48,
        }
        if foir_48 > PFL_POLICY["warn_foir"]:
            flags.append("FOIR_EXCEEDED")
        else:
            flags.append("FOIR_HIGH")

    # ── Check 5: Employment stability ─────────────────────────────────────────
    if employment_years >= 2:
        checks["employment"] = {"status": "PASS", "label": f"Stable — {employment_years:.0f} yrs ✅"}
    elif employment_years >= 1:
        checks["employment"] = {"status": "WARN", "label": f"1–2 years — PFL may ask for more docs ⚠️"}
        flags.append("SHORT_EMPLOYMENT")
    else:
        checks["employment"] = {"status": "WARN", "label": "Less than 1 year ⚠️"}
        flags.append("SHORT_EMPLOYMENT")

    # ── Check 6: Age ──────────────────────────────────────────────────────────
    loan_end_age = age + (tenure_data["tenure_months"] if tenure_data else 48) // 12
    if loan_end_age <= 60:
        checks["age"] = {"status": "PASS", "label": "Loan closes before retirement ✅"}
    else:
        checks["age"] = {"status": "WARN", "label": "Loan extends past age 60 ⚠️"}
        flags.append("AGE_RISK")

    # ── Decision logic ────────────────────────────────────────────────────────
    hard_fails = [f for f in flags if f in ("CIBIL_REJECTED", "FOIR_EXCEEDED", "INCOME_TOO_LOW")]
    soft_warns = [f for f in flags if f in ("LOW_CIBIL", "SHORT_EMPLOYMENT", "AGE_RISK", "FOIR_HIGH")]

    if not hard_fails and not soft_warns:
        decision, risk_band, rate = "GREEN",  "A", PFL_POLICY["base_rate"]
    elif not hard_fails and len(soft_warns) == 1:
        decision, risk_band, rate = "GREEN",  "B", 12.00
    elif not hard_fails and len(soft_warns) >= 2:
        decision, risk_band, rate = "YELLOW", "C", 14.00
    else:
        decision, risk_band, rate = "RED",    "D", None

    # ── Build offer ───────────────────────────────────────────────────────────
    offer = None
    if decision in ("GREEN", "YELLOW") and tenure_data:
        emi            = calc_emi(loan_amount, tenure_data["tenure_months"], rate or PFL_POLICY["base_rate"])
        processing_fee = int(loan_amount * PFL_POLICY["processing_fee"])
        offer = {
            "lender":           "Poonawalla Fincorp",
            "loan_amount":      int(loan_amount),
            "interest_rate":    rate or PFL_POLICY["base_rate"],
            "tenure_months":    tenure_data["tenure_months"],
            "emi":              emi,
            "foir":             tenure_data["foir"],
            "processing_fee":   processing_fee,
            "disbursement":     "Direct to hospital",
            "approval_time":    "Same day",
        }

    # ── Alternatives if RED ───────────────────────────────────────────────────
    alternatives = []
    if decision == "RED":
        # Option 1 — smaller loan that clears FOIR
        for smaller in [loan_amount * 0.5, loan_amount * 0.33, loan_amount * 0.25]:
            td = find_best_tenure(smaller, monthly_income, existing_emi, PFL_POLICY["base_rate"])
            if td:
                alternatives.append({
                    "type":    "smaller_loan",
                    "label":   f"Apply for ₹{smaller:,.0f} instead",
                    "amount":  int(smaller),
                    "tenure":  td["tenure_months"],
                    "emi":     calc_emi(smaller, td["tenure_months"], PFL_POLICY["base_rate"]),
                    "foir":    td["foir"],
                })
                break

        # Option 2 — co-applicant
        alternatives.append({
            "type":  "co_applicant",
            "label": "Add a co-applicant (spouse / parent)",
            "note":  "Their income is counted — FOIR drops significantly",
        })

    return {
        "decision":          decision,
        "risk_band":         risk_band,
        "checks":            checks,
        "flags":             flags,
        "offer":             offer,
        "alternatives":      alternatives,
    }


# ── Build full application package ────────────────────────────────────────────

def build_application_package(
    user_id:      str,
    profile:      dict,
    financials:   dict,
    documents:    list[dict],
    loan_amount:  float,
    tenure_months: int,
    hospital_name: str,
    procedure:    str,
    eligibility:  dict,
) -> tuple[str, dict]:
    """
    Assemble the complete application package that goes to PFL.
    Returns (reference_id, application_dict).
    """
    year    = datetime.now().year
    ref_id  = f"PFL-MED-{year}-{random.randint(10000, 99999)}"
    rate    = eligibility["offer"]["interest_rate"] if eligibility.get("offer") else PFL_POLICY["base_rate"]
    emi     = calc_emi(loan_amount, tenure_months, rate)

    doc_list = [
        {
            "doc_type": d.get("doc_type"),
            "filename":  d.get("file_name"),
            "url":       d.get("file_url"),
            "extracted": d.get("extraction_status") == "done",
        }
        for d in documents
        if d.get("file_url")   # only include docs that have a real URL
    ]

    application = {
        # Reference
        "reference_id":     ref_id,
        "user_id":          user_id,

        # Applicant
        "applicant_name":   profile.get("name"),
        "age":              profile.get("age"),
        "city":             profile.get("city"),
        "blood_group":      profile.get("blood_group"),
        "comorbidities":    profile.get("comorbidities", []),

        # Financial snapshot
        "monthly_income":   financials.get("monthly_income"),
        "existing_emi":     financials.get("existing_emi", 0),
        "cibil_score":      financials.get("cibil_score"),
        "employment_years": financials.get("employment_years", 2),
        "employment_type":  financials.get("employment_type"),

        # Loan terms
        "loan_amount":      int(loan_amount),
        "tenure_months":    tenure_months,
        "interest_rate":    rate,
        "emi":              emi,
        "processing_fee":   int(loan_amount * PFL_POLICY["processing_fee"]),
        "purpose":          "medical_treatment",

        # Medical
        "hospital_name":    hospital_name,
        "procedure":        procedure,

        # MedPath pre-assessment
        "medpath_decision": eligibility["decision"],
        "risk_band":        eligibility["risk_band"],
        "eligibility_flags": eligibility["flags"],
        "foir":             eligibility["offer"]["foir"] if eligibility.get("offer") else None,

        # Documents
        "documents":        doc_list,
    }

    return ref_id, application