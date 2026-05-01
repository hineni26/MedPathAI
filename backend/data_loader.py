import pandas as pd
import os
from math import radians, sin, cos, sqrt, atan2

# ── Load CSVs once at startup ──────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

hospitals_df  = pd.read_csv(os.path.join(DATA_DIR, "hospital_rows.csv"))
procedures_df = pd.read_csv(os.path.join(DATA_DIR, "procedures_rows.csv"))
cities_df     = pd.read_csv(os.path.join(DATA_DIR, "cities_rows.csv"))

# Normalize city_tier: tier1 → metro
hospitals_df["city_tier"] = hospitals_df["city_tier"].replace({"tier1": "metro"})

# Normalize city names to lowercase for matching
hospitals_df["city_lower"]  = hospitals_df["city"].str.lower().str.strip()
cities_df["city_lower"]     = cities_df["city"].str.lower().str.strip()
procedures_df["procedure_name"] = procedures_df["procedure_name"].str.lower().str.strip()

print(f"✅ Loaded {len(hospitals_df)} hospitals, "
      f"{len(procedures_df)} procedures, "
      f"{len(cities_df)} cities")

# ── Supported procedures ───────────────────────────────────────────────────────
SUPPORTED_PROCEDURES = [
    "angioplasty", "appendectomy", "arthroscopy", "bypass_cabg",
    "c_section", "cataract", "colonoscopy", "ct_scan", "dialysis_single",
    "ecg_echo", "endoscopy", "gallbladder_surgery", "hernia_repair",
    "hip_replacement", "hysterectomy", "kidney_stone_removal",
    "knee_replacement", "lasik", "mri_scan", "normal_delivery"
]

# ── Comorbidity cost multipliers ───────────────────────────────────────────────
COMORBIDITY_MULTIPLIERS = {
    "diabetes":        {"cost_add": 0.12, "icu_risk": 0.18, "label": "Diabetes"},
    "hypertension":    {"cost_add": 0.08, "icu_risk": 0.10, "label": "Hypertension"},
    "cardiac_history": {"cost_add": 0.18, "icu_risk": 0.35, "label": "Cardiac History"},
    "kidney_disease":  {"cost_add": 0.22, "icu_risk": 0.20, "label": "Kidney Disease"},
    "asthma":          {"cost_add": 0.06, "icu_risk": 0.08, "label": "Asthma"},
    "obesity":         {"cost_add": 0.10, "icu_risk": 0.12, "label": "Obesity"},
}

# ── Cost component splits ──────────────────────────────────────────────────────
COST_COMPONENTS = {
    "procedure":     0.55,
    "doctor_fees":   0.12,
    "hospital_stay": 0.16,
    "diagnostics":   0.10,
    "medicines":     0.05,
    "contingency":   0.02,
}

# ── Helper: Haversine distance (km) ───────────────────────────────────────────
def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1)*cos(lat2)*sin(dlon/2)**2
    return R * 2 * atan2(sqrt(a), sqrt(1 - a))

# ── Get city info ──────────────────────────────────────────────────────────────
def get_city_info(city_name: str) -> dict | None:
    match = cities_df[cities_df["city_lower"] == city_name.lower().strip()]
    if match.empty:
        # fuzzy fallback — check if city_name is contained
        match = cities_df[cities_df["city_lower"].str.contains(
            city_name.lower().strip(), na=False)]
    if match.empty:
        return None
    row = match.iloc[0]
    return {
        "city_id":   row["city_id"],
        "city":      row["city"],
        "state":     row["state"],
        "tier":      row["tier"],
        "latitude":  row["latitude"],
        "longitude": row["longitude"],
    }

# ── Get hospitals by city ──────────────────────────────────────────────────────
def get_hospitals_by_city(city_name: str) -> pd.DataFrame:
    return hospitals_df[
        hospitals_df["city_lower"] == city_name.lower().strip()
    ].copy()

# ── Get procedures for a hospital ─────────────────────────────────────────────
def get_procedure_for_hospital(hospital_id: str, procedure_name: str) -> dict | None:
    match = procedures_df[
        (procedures_df["hospital_id"] == hospital_id) &
        (procedures_df["procedure_name"] == procedure_name.lower().strip())
    ]
    if match.empty:
        return None
    row = match.iloc[0]
    return {
        "procedure_id":                row["procedure_id"],
        "min_cost_inr":                int(row["min_cost_inr"]),
        "max_cost_inr":                int(row["max_cost_inr"]),
        "avg_cost_inr":                int(row["avg_cost_inr"]),
        "success_rate":                float(row["success_rate"]),
        "avg_recovery_days":           int(row["avg_recovery_days"]),
        "insurance_covered":           bool(row["insurance_covered"]),
        "specialists_count":           int(row["specialists_count"]),
        "specialization_match":        bool(row["specialization_match"]),
        "annual_procedure_volume":     int(row["annual_procedure_volume"]),
        "procedure_waiting_time_days": int(row["procedure_waiting_time_days"]),
        "avg_specialist_availability": float(row["avg_specialist_availability"]),
        "specialization_relevance_score": float(row["specialization_relevance_score"]),
    }

# ── Score a single hospital ────────────────────────────────────────────────────
def score_hospital(hospital: dict, procedure: dict, budget: int | None,
                   deadline_days: int | None, is_emergency: bool) -> float:

    # Emergency: only care about ICU + 24x7
    if is_emergency:
        score = 0.0
        if hospital.get("emergency_24x7"):    score += 40
        if hospital.get("inhouse_critical_care"): score += 30
        if hospital.get("icu_beds", 0) > 50:  score += 20
        score += (hospital.get("rating", 3) / 5.0) * 10
        return round(score, 2)

    # Standard scoring
    spec   = procedure["specialization_relevance_score"] * 30
    rating = (hospital.get("rating", 3) / 5.0) * 20
    nabh   = 15 if hospital.get("nabh_accredited") else 0
    insur  = 5  if procedure["insurance_covered"] else 0

    # Budget fit
    if budget and procedure["min_cost_inr"] > budget:
        budget_score = 0   # over budget — still show but score 0 here
    else:
        budget_score = 20

    # Waiting time (lower is better, max 30 days reference)
    wait   = procedure["procedure_waiting_time_days"]
    wait_score = max(0, (1 - wait / 30)) * 10

    # Deadline filter
    if deadline_days is not None and wait > deadline_days:
        return -1  # exclude — cannot make deadline

    total = spec + rating + nabh + insur + budget_score + wait_score
    return round(total, 2)

# ── Main search function ───────────────────────────────────────────────────────
def search_hospitals(
    city: str,
    procedure_name: str,
    budget: int | None = None,
    deadline_days: int | None = None,
    is_emergency: bool = False,
    user_lat: float | None = None,
    user_lon: float | None = None,
    limit: int = 3
) -> list[dict]:

    city_hospitals = get_hospitals_by_city(city)
    if city_hospitals.empty:
        return []

    results = []
    over_budget = []

    for _, hosp_row in city_hospitals.iterrows():
        hosp = hosp_row.to_dict()
        proc = get_procedure_for_hospital(hosp["hospital_id"], procedure_name)
        if proc is None:
            continue

        score = score_hospital(hosp, proc, budget, deadline_days, is_emergency)
        if score == -1:
            continue  # misses deadline — exclude

        # Distance
        if user_lat and user_lon:
            dist = haversine(user_lat, user_lon,
                             hosp["latitude"], hosp["longitude"])
        else:
            dist = None

        entry = {
            "hospital_id":         hosp["hospital_id"],
            "hospital_name":       hosp["hospital_name"],
            "chain":               hosp["chain"],
            "city":                hosp["city"],
            "rating":              hosp["rating"],
            "nabh_accredited":     bool(hosp["nabh_accredited"]),
            "jci_accredited":      bool(hosp["jci_accredited"]),
            "beds":                int(hosp["beds"]),
            "icu_beds":            int(hosp["icu_beds"]),
            "emergency_24x7":      bool(hosp["emergency_24x7"]),
            "ambulance_available": bool(hosp["ambulance_available"]),
            "cashless_insurance":  bool(hosp["cashless_insurance"]),
            "inhouse_critical_care": bool(hosp["inhouse_critical_care"]),
            "consultation_fee_inr": int(hosp["consultation_fee_inr"]),
            "distance_km":         round(dist, 1) if dist else None,
            "score":               score,
            "over_budget":         bool(budget and proc["min_cost_inr"] > budget),
            "procedure":           proc,
        }

        if entry["over_budget"] and not is_emergency:
            over_budget.append(entry)
        else:
            results.append(entry)

    # Sort within budget by score
    results.sort(key=lambda x: x["score"], reverse=True)
    top = results[:limit]

    # Always add best over-budget hospital if we have room or it's top rated
    if over_budget:
        over_budget.sort(key=lambda x: x["score"], reverse=True)
        best_over = over_budget[0]
        best_over["over_budget_label"] = "⚠️ Over budget — highest rated"
        top.append(best_over)

    return top

# ── Calculate cost breakdown ───────────────────────────────────────────────────
def calculate_cost_breakdown(
    procedure: dict,
    comorbidities: list[str],
    age: int | None,
    insurance_coverage: int = 0
) -> dict:

    base_min = procedure["min_cost_inr"]
    base_max = procedure["max_cost_inr"]
    base_avg = procedure["avg_cost_inr"]

    # Comorbidity multiplier
    multiplier = 1.0
    risk_flags = []
    for c in comorbidities:
        m = COMORBIDITY_MULTIPLIERS.get(c.lower(), {})
        multiplier += m.get("cost_add", 0)
        if m.get("icu_risk", 0) > 0.2:
            risk_flags.append(f"{m.get('label', c)} may require ICU monitoring")

    # Age adjustment
    if age and age > 65:
        multiplier += 0.10
        risk_flags.append("Age >65 increases recovery complexity")
    elif age and age > 50:
        multiplier += 0.05

    # Confidence — widen range if missing info
    missing = sum(1 for v in [age] if v is None)
    margin  = 0.15 + missing * 0.05

    adj_min = int(base_min * multiplier * (1 - margin))
    adj_max = int(base_max * multiplier * (1 + margin))
    adj_avg = int(base_avg * multiplier)

    # Component breakdown
    breakdown = {}
    for component, pct in COST_COMPONENTS.items():
        breakdown[component] = {
            "min": int(adj_min * pct),
            "max": int(adj_max * pct),
        }

    # Insurance gap
    you_pay_min = max(0, adj_min - insurance_coverage)
    you_pay_max = max(0, adj_max - insurance_coverage)

    return {
        "breakdown":        breakdown,
        "total_min":        adj_min,
        "total_max":        adj_max,
        "total_avg":        adj_avg,
        "confidence":       round(1.0 - margin, 2),
        "insurance_covers": insurance_coverage,
        "you_pay_min":      you_pay_min,
        "you_pay_max":      you_pay_max,
        "risk_flags":       risk_flags,
        "multiplier_applied": round(multiplier, 2),
    }

# ── PFL EMI Calculator ─────────────────────────────────────────────────────────
PFL_RATE_ANNUAL = 0.0999

def calculate_pfl_emi(principal: int, months: int) -> int:
    r = PFL_RATE_ANNUAL / 12
    if principal <= 0:
        return 0
    emi = principal * r * (1 + r)**months / ((1 + r)**months - 1)
    return int(round(emi))

def calculate_pfl_options(loan_amount: int) -> dict:
    return {
        "loan_amount":   loan_amount,
        "interest_rate": "9.99% p.a.",
        "provider":      "Poonawalla Fincorp",
        "emi_12_months": calculate_pfl_emi(loan_amount, 12),
        "emi_24_months": calculate_pfl_emi(loan_amount, 24),
        "emi_36_months": calculate_pfl_emi(loan_amount, 36),
        "max_loan":      "₹30 Lakh (Personal) / ₹10 Crore (Medical Equipment)",
        "cta":           "Apply at Poonawalla Fincorp",
    }

# ── Loan Eligibility Check ─────────────────────────────────────────────────────
def check_loan_eligibility(
    loan_amount: int,
    monthly_income: int,
    existing_emi: int,
    cibil_score: int,
    employment_years: float
) -> dict:

    proposed_emi = calculate_pfl_emi(loan_amount, 24)
    total_emi    = existing_emi + proposed_emi
    foir         = total_emi / monthly_income if monthly_income > 0 else 1.0
    max_eligible = monthly_income * 10

    score = 0
    flags = []

    # FOIR scoring
    if foir <= 0.30:   score += 40
    elif foir <= 0.40: score += 25
    elif foir <= 0.50: score += 10
    else:
        score += 0
        flags.append(f"FOIR too high: {round(foir*100)}% (limit 50%)")

    # CIBIL scoring
    if cibil_score >= 750:   score += 30
    elif cibil_score >= 700: score += 20
    elif cibil_score >= 650: score += 10
    else:
        flags.append(f"CIBIL score {cibil_score} is below preferred 700")

    # Employment
    if employment_years >= 3:   score += 20
    elif employment_years >= 1: score += 12
    else:
        score += 0
        flags.append("Less than 1 year employment — stability concern")

    # Loan vs income
    if loan_amount <= max_eligible: score += 10
    else:
        flags.append(f"Loan amount exceeds 10x monthly income")

    # Decision
    if score >= 70:   decision = "GREEN"
    elif score >= 45: decision = "YELLOW"
    else:             decision = "RED"

    pfl_recommendation = {
        "GREEN":  "Pre-approved — details sent to Poonawalla Fincorp",
        "YELLOW": "Likely eligible — income verification recommended",
        "RED":    "May not qualify — consider co-applicant or smaller loan",
    }

    return {
        "score":            score,
        "decision":         decision,
        "foir":             round(foir, 2),
        "foir_pct":         f"{round(foir * 100)}%",
        "max_eligible":     min(max_eligible, 3000000),
        "proposed_emi":     proposed_emi,
        "total_emi_after":  total_emi,
        "flags":            flags,
        "recommendation":   pfl_recommendation[decision],
    }