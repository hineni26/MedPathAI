from data_loader import (
    search_hospitals,
    get_city_info,
    SUPPORTED_PROCEDURES
)

def run_provider_node(state: dict) -> dict:
    """
    Finds and scores hospitals based on extracted intent.
    Pure Python — no Gemini call.
    Returns updated state with ranked hospital list.
    """
    nodes_visited = state.get("nodes_visited", [])
    nodes_visited.append("provider")

    procedure     = state.get("procedure")
    city          = state.get("city")
    budget        = state.get("budget")
    deadline_days = state.get("deadline_days")
    is_emergency  = state.get("is_emergency", False)
    profile       = state.get("user_profile", {})

    # Fallback to profile city if not extracted
    if not city:
        city = profile.get("city")

    # If still no city
    if not city:
        return {
            **state,
            "hospitals":      [],
            "provider_error": "Could not determine city. Please specify your city.",
            "nodes_visited":  nodes_visited,
        }

    # Get city info (lat/lng for distance)
    city_info = get_city_info(city)
    user_lat = state.get("user_lat") or (city_info["latitude"]  if city_info else None)
    user_lon = state.get("user_lon") or (city_info["longitude"] if city_info else None)

    # If emergency and no procedure — default to angioplasty
    # (most common cardiac emergency procedure)
    if is_emergency and not procedure:
        procedure = "angioplasty"

    # If still no procedure
    if not procedure:
        return {
            **state,
            "hospitals":      [],
            "provider_error": "Could not determine procedure.",
            "nodes_visited":  nodes_visited,
        }

    # Search hospitals
    hospitals = search_hospitals(
        city          = city,
        procedure_name= procedure,
        budget        = budget,
        deadline_days = deadline_days,
        is_emergency  = is_emergency,
        user_lat      = user_lat,
        user_lon      = user_lon,
        limit         = 3,
    )

    # Format for frontend
    formatted = []
    for h in hospitals:
        proc = h.get("procedure", {})
        formatted.append({
            "hospital_id":      h["hospital_id"],
            "hospital_name":    h["hospital_name"],
            "chain":            h["chain"],
            "city":             h["city"],
            "rating":           h["rating"],
            "nabh_accredited":  h["nabh_accredited"],
            "jci_accredited":   h["jci_accredited"],
            "beds":             h["beds"],
            "icu_beds":         h["icu_beds"],
            "emergency_24x7":   h["emergency_24x7"],
            "ambulance":        h["ambulance_available"],
            "cashless_insurance": h["cashless_insurance"],
            "inhouse_critical_care": h["inhouse_critical_care"],
            "consultation_fee": h["consultation_fee_inr"],
            "distance_km":      h["distance_km"],
            "score":            h["score"],
            "over_budget":      h["over_budget"],
            "over_budget_label": h.get("over_budget_label"),

            # Procedure details
            "procedure_name":        procedure,
            "cost_min":              proc.get("min_cost_inr"),
            "cost_max":              proc.get("max_cost_inr"),
            "cost_avg":              proc.get("avg_cost_inr"),
            "success_rate":          proc.get("success_rate"),
            "waiting_days":          proc.get("procedure_waiting_time_days"),
            "avg_recovery_days":     proc.get("avg_recovery_days"),
            "insurance_covered":     proc.get("insurance_covered"),
            "specialists_count":     proc.get("specialists_count"),
            "annual_volume":         proc.get("annual_procedure_volume"),
            "relevance_score":       proc.get("specialization_relevance_score"),
        })

    return {
        **state,
        "hospitals":      formatted,
        "city_info":      city_info,
        "procedure":      procedure,
        "nodes_visited":  nodes_visited,
        "provider_error": None,
    }