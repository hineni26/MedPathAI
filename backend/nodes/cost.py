from data_loader import (
    calculate_cost_breakdown,
    calculate_pfl_options,
    check_loan_eligibility,
    COMORBIDITY_MULTIPLIERS
)

def run_cost_node(state: dict) -> dict:
    """
    Calculates full cost breakdown, PFL EMI options, and loan eligibility.
    Pure Python — no Gemini call.
    Runs after user selects a hospital.
    """
    nodes_visited = state.get("nodes_visited", [])
    nodes_visited.append("cost")

    profile       = state.get("user_profile", {})
    financials    = state.get("user_financials", {})
    selected      = state.get("selected_hospital")
    hospitals     = state.get("hospitals", [])

    # Get selected hospital — either explicitly selected or top result
    if selected:
        hospital = next(
            (h for h in hospitals if h["hospital_id"] == selected),
            hospitals[0] if hospitals else None
        )
    else:
        hospital = hospitals[0] if hospitals else None

    if not hospital:
        return {
            **state,
            "cost_result":  None,
            "pfl_options":  None,
            "loan_eligibility": None,
            "nodes_visited": nodes_visited,
        }

    # ── Build procedure dict for cost calculation ──────────────────────────────
    procedure = {
        "min_cost_inr":              hospital["cost_min"],
        "max_cost_inr":              hospital["cost_max"],
        "avg_cost_inr":              hospital["cost_avg"],
        "success_rate":              hospital.get("success_rate", 0.9),
        "avg_recovery_days":         hospital.get("avg_recovery_days", 5),
        "insurance_covered":         hospital.get("insurance_covered", False),
        "procedure_waiting_time_days": hospital.get("waiting_days", 3),
    }

    # ── Get user details from profile ──────────────────────────────────────────
    comorbidities      = profile.get("comorbidities", [])
    age                = profile.get("age")
    insurance_provider = profile.get("insurance_provider")
    insurance_coverage = profile.get("insurance_coverage", 0)

    # ── Calculate cost breakdown ───────────────────────────────────────────────
    cost_result = calculate_cost_breakdown(
        procedure         = procedure,
        comorbidities     = comorbidities,
        age               = age,
        insurance_coverage= insurance_coverage,
    )

    
    

    # Fallback if you_pay_avg not present
    loan_amount = int((cost_result["you_pay_min"] + cost_result["you_pay_max"]) / 2)

    # ── PFL EMI options ────────────────────────────────────────────────────────
    pfl_options = calculate_pfl_options(loan_amount)

    # ── Loan eligibility check (if financials available) ──────────────────────
    loan_eligibility = None
    if financials and financials.get("monthly_income"):
        loan_eligibility = check_loan_eligibility(
            loan_amount      = loan_amount,
            monthly_income   = financials.get("monthly_income", 0),
            existing_emi     = financials.get("existing_emi", 0),
            cibil_score      = financials.get("cibil_score", 700),
            employment_years = financials.get("employment_years", 2),
        )
    else:
        # No financials uploaded yet — show generic eligibility
        loan_eligibility = {
            "decision":       "UNKNOWN",
            "recommendation": "Upload your financial documents in My Documents to get instant pre-approval",
            "flags":          [],
            "foir":           None,
            "score":          None,
        }

    # ── Build comorbidity warnings ─────────────────────────────────────────────
    comorbidity_warnings = []
    for c in comorbidities:
        m = COMORBIDITY_MULTIPLIERS.get(c.lower(), {})
        if m:
            pct = int(m.get("cost_add", 0) * 100)
            comorbidity_warnings.append(
                f"{m.get('label', c)} may add ~{pct}% to total cost"
            )

    # ── Final cost result ──────────────────────────────────────────────────────
    cost_result["comorbidity_warnings"] = comorbidity_warnings
    cost_result["insurance_provider"]   = insurance_provider
    cost_result["selected_hospital"]    = {
        "hospital_id":   hospital["hospital_id"],
        "hospital_name": hospital["hospital_name"],
        "procedure":     hospital["procedure_name"],
        "success_rate":  hospital.get("success_rate"),
        "recovery_days": hospital.get("avg_recovery_days"),
        "waiting_days":  hospital.get("waiting_days"),
    }

    return {
        **state,
        "cost_result":      cost_result,
        "pfl_options":      pfl_options,
        "loan_eligibility": loan_eligibility,
        "loan_amount":      loan_amount,
        "nodes_visited":    nodes_visited,
    }