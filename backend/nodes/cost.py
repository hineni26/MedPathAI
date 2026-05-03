import os
import json
import google.generativeai as genai
from dotenv import load_dotenv
from data_loader import (
    COMORBIDITY_MULTIPLIERS,
    calculate_cost_breakdown,
    calculate_pfl_options,
    check_loan_eligibility,
)

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
_gemini = genai.GenerativeModel("gemini-2.5-flash")

# ── Gemini cost estimator for unmapped procedures ─────────────────────────────

_ESTIMATE_PROMPT = """
You are a medical cost estimation expert for Indian hospitals.
Given the clinical and hospital context below, return realistic cost estimates.

Clinical context:
- Symptom summary: {symptom_summary}
- Possible causes / clinical signals: {possible_causes}
- ICD-10 code: {icd10_code}
- Procedure (if known): {procedure_name}

Hospital context:
- Hospital: {hospital_name}
- City: {city}
- NABH accredited: {nabh}
- JCI accredited: {jci}
- Rating: {rating}/5
- Beds: {beds}

Patient context:
- Age: {age}
- Comorbidities: {comorbidities}

Return ONLY valid JSON, no markdown, no explanation:
{{
  "cost_min_inr": <integer>,
  "cost_max_inr": <integer>,
  "avg_cost_inr": <integer>,
  "waiting_days": <integer, typical wait for this type of care>,
  "success_rate": <float 0.0-1.0>,
  "avg_recovery_days": <integer>
}}

Rules:
- Use realistic Indian private hospital costs in INR.
- If the clinical signal is a diagnostic/imaging need (e.g. scan, echo), costs are lower (5,000–30,000).
- If it's a major surgery, costs are higher (80,000–5,00,000).
- NABH/JCI accredited hospitals typically cost 15–25% more.
- Higher-rated hospitals (4.5+) skew toward the upper end.
- waiting_days: 1-3 for diagnostics, 3-14 for elective surgeries.
- Return ONLY the JSON object.
"""


def _gemini_estimate_costs(hospital: dict, profile: dict, symptom_ctx: dict) -> dict | None:
    """Call Gemini to approximate cost fields when DB has no procedure match."""
    prompt = _ESTIMATE_PROMPT.format(
        symptom_summary=symptom_ctx.get("symptom_summary") or "not specified",
        possible_causes=", ".join(symptom_ctx.get("possible_causes") or []) or "not specified",
        icd10_code=symptom_ctx.get("icd10_code") or "unknown",
        procedure_name=hospital.get("procedure_name") or "not mapped",
        hospital_name=hospital.get("hospital_name", "unknown"),
        city=hospital.get("city", "unknown"),
        nabh=hospital.get("nabh_accredited", False),
        jci=hospital.get("jci_accredited", False),
        rating=hospital.get("rating", "unknown"),
        beds=hospital.get("beds", "unknown"),
        age=profile.get("age", "unknown"),
        comorbidities=", ".join(profile.get("comorbidities") or []) or "none",
    )
    try:
        raw = _gemini.generate_content(prompt).text.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        data = json.loads(raw.strip())
        return {
            "cost_min_inr":      int(data["cost_min_inr"]),
            "cost_max_inr":      int(data["cost_max_inr"]),
            "avg_cost_inr":      int(data["avg_cost_inr"]),
            "waiting_days":      int(data.get("waiting_days", 7)),
            "success_rate":      float(data.get("success_rate", 0.85)),
            "avg_recovery_days": int(data.get("avg_recovery_days", 5)),
        }
    except Exception as e:
        print(f"❌ _gemini_estimate_costs error: {e}")
        return None


# ── Per-hospital cost estimator ───────────────────────────────────────────────

def _estimate_for_hospital(
    hospital: dict,
    profile: dict,
    financials: dict,
    symptom_ctx: dict | None = None,
) -> dict:
    """Build cost, financing, and eligibility for one hospital card."""

    cost_min = hospital.get("cost_min")
    cost_max = hospital.get("cost_max")
    cost_avg = hospital.get("cost_avg")
    is_estimated = False

    # ── If DB has no cost data, ask Gemini to approximate ────────────────────
    if not all(v is not None for v in (cost_min, cost_max, cost_avg)):
        estimated = _gemini_estimate_costs(hospital, profile, symptom_ctx or {})
        if estimated:
            cost_min  = estimated["cost_min_inr"]
            cost_max  = estimated["cost_max_inr"]
            cost_avg  = estimated["avg_cost_inr"]
            is_estimated = True
            # Back-fill waiting/recovery so selected_hospital block is complete
            if hospital.get("waiting_days") is None:
                hospital = {**hospital, "waiting_days": estimated["waiting_days"]}
            if hospital.get("avg_recovery_days") is None:
                hospital = {**hospital, "avg_recovery_days": estimated["avg_recovery_days"]}
            if hospital.get("success_rate") is None:
                hospital = {**hospital, "success_rate": estimated["success_rate"]}
        else:
            # Gemini also failed — return nothing (same as before, last resort)
            return {
                "cost_result": None,
                "pfl_options": None,
                "loan_eligibility": None,
                "loan_amount": None,
            }

    procedure = {
        "min_cost_inr":                  cost_min,
        "max_cost_inr":                  cost_max,
        "avg_cost_inr":                  cost_avg,
        "success_rate":                  hospital.get("success_rate", 0.9),
        "avg_recovery_days":             hospital.get("avg_recovery_days", 5),
        "insurance_covered":             hospital.get("insurance_covered", False),
        "procedure_waiting_time_days":   hospital.get("waiting_days", 3),
    }

    comorbidities = profile.get("comorbidities", [])
    cost_result = calculate_cost_breakdown(
        procedure=procedure,
        comorbidities=comorbidities,
        age=profile.get("age"),
        insurance_coverage=profile.get("insurance_coverage", 0),
    )

    # Tag AI-estimated results so the frontend can show a disclaimer
    cost_result["is_estimated"] = is_estimated
    if is_estimated:
        cost_result["estimated_disclaimer"] = (
            "Costs are AI-estimated — no exact procedure match found in database. "
            "Verify with the hospital before proceeding."
        )

    loan_amount = int((cost_result["you_pay_min"] + cost_result["you_pay_max"]) / 2)
    pfl_options = calculate_pfl_options(loan_amount)

    if financials and financials.get("monthly_income"):
        loan_eligibility = check_loan_eligibility(
            loan_amount=loan_amount,
            monthly_income=financials.get("monthly_income", 0),
            existing_emi=financials.get("existing_emi", 0),
            cibil_score=financials.get("cibil_score", 700),
            employment_years=financials.get("employment_years", 2),
        )
    else:
        loan_eligibility = {
            "decision": "UNKNOWN",
            "recommendation": "Upload your financial documents in My Documents to get instant pre-approval",
            "flags": [],
            "foir": None,
            "score": None,
        }

    comorbidity_warnings = []
    for c in comorbidities:
        m = COMORBIDITY_MULTIPLIERS.get(c.lower(), {})
        if m:
            pct = int(m.get("cost_add", 0) * 100)
            comorbidity_warnings.append(
                f"{m.get('label', c)} may add ~{pct}% to total cost"
            )

    cost_result["comorbidity_warnings"] = comorbidity_warnings
    cost_result["insurance_provider"] = profile.get("insurance_provider")
    cost_result["selected_hospital"] = {
        "hospital_id":   hospital["hospital_id"],
        "hospital_name": hospital["hospital_name"],
        "procedure":     hospital.get("procedure_name"),
        "success_rate":  hospital.get("success_rate"),
        "recovery_days": hospital.get("avg_recovery_days"),
        "waiting_days":  hospital.get("waiting_days"),
    }

    return {
        "cost_result":      cost_result,
        "pfl_options":      pfl_options,
        "loan_eligibility": loan_eligibility,
        "loan_amount":      loan_amount,
    }


# ── Graph node ────────────────────────────────────────────────────────────────

def run_cost_node(state: dict) -> dict:
    """
    Calculates hospital-specific cost breakdowns, PFL EMI options, and loan
    eligibility. Each returned hospital gets its own estimate, so the frontend
    can swap breakdowns instantly when the user clicks a hospital card.
    """
    nodes_visited = state.get("nodes_visited", [])
    nodes_visited.append("cost")

    profile    = state.get("user_profile", {})
    financials = state.get("user_financials", {})
    selected   = state.get("selected_hospital")
    hospitals  = state.get("hospitals", [])

    # Symptom context for Gemini estimator
    symptom_ctx = {
        "symptom_summary": state.get("symptom_summary"),
        "possible_causes": state.get("possible_causes", []),
        "icd10_code":      state.get("icd10_code"),
    }

    if not hospitals:
        return {
            **state,
            "cost_result":               None,
            "pfl_options":               None,
            "loan_eligibility":          None,
            "cost_results_by_hospital":  {},
            "pfl_options_by_hospital":   {},
            "loan_eligibility_by_hospital": {},
            "nodes_visited":             nodes_visited,
        }

    estimates_by_hospital = {
        hospital["hospital_id"]: _estimate_for_hospital(
            hospital, profile, financials, symptom_ctx
        )
        for hospital in hospitals
    }

    hospital = hospitals[0]
    if selected:
        hospital = next(
            (h for h in hospitals if h["hospital_id"] == selected),
            hospitals[0],
        )

    for h in hospitals:
        estimate = estimates_by_hospital[h["hospital_id"]]
        h["cost_result"]      = estimate["cost_result"]
        h["pfl_options"]      = estimate["pfl_options"]
        h["loan_eligibility"] = estimate["loan_eligibility"]
        h["loan_amount"]      = estimate["loan_amount"]

    selected_estimate = estimates_by_hospital[hospital["hospital_id"]]

    return {
        **state,
        "hospitals":      hospitals,
        "cost_result":    selected_estimate["cost_result"],
        "pfl_options":    selected_estimate["pfl_options"],
        "loan_eligibility": selected_estimate["loan_eligibility"],
        "loan_amount":    selected_estimate["loan_amount"],
        "cost_results_by_hospital": {
            hid: est["cost_result"]
            for hid, est in estimates_by_hospital.items()
            if est["cost_result"] is not None
        },
        "pfl_options_by_hospital": {
            hid: est["pfl_options"]
            for hid, est in estimates_by_hospital.items()
            if est["pfl_options"] is not None
        },
        "loan_eligibility_by_hospital": {
            hid: est["loan_eligibility"]
            for hid, est in estimates_by_hospital.items()
            if est["loan_eligibility"] is not None
        },
        "nodes_visited": nodes_visited,
    }