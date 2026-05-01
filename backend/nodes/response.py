PROCEDURE_LABELS = {
    "angioplasty": "Angioplasty",
    "appendectomy": "Appendectomy",
    "arthroscopy": "Arthroscopy",
    "bypass_cabg": "Bypass CABG",
    "c_section": "C-section",
    "cataract": "Cataract Surgery",
    "colonoscopy": "Colonoscopy",
    "ct_scan": "CT Scan",
    "dialysis_single": "Dialysis",
    "ecg_echo": "ECG/Echo Evaluation",
    "endoscopy": "Endoscopy",
    "gallbladder_surgery": "Gallbladder Surgery",
    "hernia_repair": "Hernia Repair",
    "hip_replacement": "Hip Replacement",
    "hysterectomy": "Hysterectomy",
    "kidney_stone_removal": "Kidney Stone Removal",
    "knee_replacement": "Knee Replacement",
    "lasik": "LASIK",
    "mri_scan": "MRI Scan",
    "normal_delivery": "Normal Delivery",
}

DEFAULT_CAUSES = [
    "Condition needing doctor evaluation",
    "Infection or inflammation",
    "Muscle strain or stress-related pain",
]

COMORBIDITY_LABELS = {
    "diabetes": "diabetes",
    "hypertension": "hypertension",
    "cardiac_history": "cardiac history",
    "kidney_disease": "kidney disease",
    "asthma": "asthma",
    "obesity": "obesity",
}


def _humanize(value: str | None) -> str:
    if not value:
        return ""
    text = str(value).replace("_", " ").replace("-", " ").strip()
    return text[:1].upper() + text[1:]


def _sentence_case(value: str | None) -> str:
    text = str(value or "").strip()
    return text[:1].upper() + text[1:] if text else ""


def _first_name(profile: dict) -> str:
    name = (profile.get("name") or "there").strip()
    return name.split()[0] if name else "there"


def _format_list(items: list[str]) -> str:
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    if len(items) == 2:
        return f"{items[0]} and {items[1]}"
    return f"{', '.join(items[:-1])}, and {items[-1]}"


def _clean_causes(causes: list[str]) -> list[str]:
    cleaned = []
    for cause in causes or []:
        label = _humanize(cause)
        if label and label.lower() not in {c.lower() for c in cleaned}:
            cleaned.append(label)

    for cause in DEFAULT_CAUSES:
        if len(cleaned) >= 3:
            break
        if cause.lower() not in {c.lower() for c in cleaned}:
            cleaned.append(cause)

    return cleaned[:3]


def _format_inr(value) -> str:
    if value is None:
        return "N/A"

    try:
        amount = int(value)
    except (TypeError, ValueError):
        return "N/A"

    return f"₹{amount:,}"


def _format_range(min_value, max_value) -> str:
    return f"{_format_inr(min_value)} – {_format_inr(max_value)}"


def _hospital_strengths(hospital: dict) -> str:
    strengths = []
    if hospital.get("annual_volume") and hospital["annual_volume"] >= 150:
        strengths.append("high procedure volume")
    if hospital.get("relevance_score") and hospital["relevance_score"] >= 0.8:
        strengths.append("specialization match")
    if hospital.get("emergency_24x7"):
        strengths.append("24/7 emergency support")
    if hospital.get("nabh_accredited"):
        strengths.append("NABH accredited")
    if hospital.get("cashless_insurance"):
        strengths.append("cashless insurance support")

    return _format_list(strengths[:2]) if strengths else "Relevant department availability"


def _format_distance(hospital: dict) -> str:
    distance = hospital.get("distance_km")
    return f"{distance} km" if distance is not None else "Distance unavailable"


def _condition_label(causes: list[str]) -> str:
    if not causes:
        return "Condition requiring clinical evaluation"
    return causes[0]


def _component_range(cost_result: dict, key: str) -> str:
    component = (cost_result or {}).get("breakdown", {}).get(key, {})
    return _format_range(component.get("min"), component.get("max"))


def _build_hospital_lines(hospitals: list[dict]) -> list[str]:
    if not hospitals:
        return ["- No matching hospitals found in the current database for this city/procedure."]

    lines = []
    for hospital in hospitals[:3]:
        lines.extend([
            f"- {hospital.get('hospital_name', 'Hospital')}, {hospital.get('city', 'your city')}",
            f"  Rating: {hospital.get('rating', 'N/A')}",
            f"  Estimated Cost Range: {_format_range(hospital.get('cost_min'), hospital.get('cost_max'))}",
            f"  Key Strengths: {_hospital_strengths(hospital)}",
            f"  Distance: {_format_distance(hospital)}",
            "",
        ])
    if lines and lines[-1] == "":
        lines.pop()
    return lines


def _build_notes(profile: dict, cost_result: dict, state: dict) -> list[str]:
    notes = [
        "This is decision support only, not a diagnosis or treatment advice",
        "Symptom-to-condition mapping can be incorrect and needs clinician review",
    ]

    risk_flags = (cost_result or {}).get("risk_flags", [])
    notes.extend(risk_flags[:2])

    comorbidities = [
        COMORBIDITY_LABELS.get(str(item).lower(), _humanize(item))
        for item in profile.get("comorbidities", [])
        if item
    ]
    if comorbidities:
        notes.append(f"{_format_list(comorbidities)} may lengthen recovery time or increase care complexity")

    if state.get("provider_error"):
        notes.append(state["provider_error"])

    return notes


def _build_assessment_message(state: dict) -> str:
    profile = state.get("user_profile", {})
    procedure = state.get("procedure")
    causes = _clean_causes(state.get("possible_causes", []))
    condition = _condition_label(causes)
    procedure_label = PROCEDURE_LABELS.get(procedure, _humanize(procedure) or "medical")
    cost_result = state.get("cost_result") or {}
    confidence = cost_result.get("confidence")
    confidence = confidence if confidence is not None else max(0.3, 1 - (state.get("ambiguity_score", 0.5) or 0.5))

    lines = [
        f"Condition: {condition}",
        f"Recommended Procedure: {procedure_label}",
        "",
        f"Confidence Score: {confidence:.2f}",
        "",
        "Notes:",
    ]

    lines.extend(f"- {_sentence_case(note)}" for note in _build_notes(profile, cost_result, state))

    return "\n".join(lines)


def _build_chat_recommendation(state: dict) -> str:
    profile = state.get("user_profile", {})
    name = _first_name(profile)
    city = state.get("city") or profile.get("city") or "your city"
    hospitals = state.get("hospitals", [])
    cost_result = state.get("cost_result") or {}
    loan_eligibility = state.get("loan_eligibility") or {}
    causes = _clean_causes(state.get("possible_causes", []))

    symptom_summary = (state.get("symptom_summary") or state.get("user_input") or "").strip().rstrip(".")
    symptom_phrase = (
        symptom_summary[:1].lower() + symptom_summary[1:]
        if symptom_summary
        else "these symptoms"
    )

    likely_clause = ""
    if causes:
        likely_conditions = (
            f"{causes[0]} or {causes[1]}"
            if len(causes) > 1
            else causes[0]
        )
        likely_clause = (
            f" This type of symptom could potentially be due to conditions like {likely_conditions}."
        )

    urgent_clause = ""
    if state.get("is_emergency"):
        urgent_clause = " Because there may be urgent warning signs, please seek immediate medical care."

    if hospitals:
        top_hospital = hospitals[0].get("hospital_name", "the top listed hospital")
        hospital_clause = (
            f" We found {len(hospitals)} hospitals in {city}, with {top_hospital} being a top option,"
        )
    else:
        hospital_clause = f" I could not find matching hospitals in {city} in the current database,"

    cost_clause = ""
    if cost_result.get("total_min") is not None and cost_result.get("total_max") is not None:
        cost_clause = (
            f" and estimated costs for the procedure range from "
            f"{_format_inr(cost_result.get('total_min'))} to {_format_inr(cost_result.get('total_max'))}."
        )
    else:
        cost_clause = " and cost estimates are not available yet."

    loan_decision = loan_eligibility.get("decision")
    if loan_decision and loan_decision != "UNKNOWN":
        financing_clause = (
            f" You are eligible for financing with a {loan_decision} loan eligibility status."
        )
    elif loan_decision == "UNKNOWN":
        financing_clause = " Financing eligibility can be checked after your financial details are available."
    else:
        financing_clause = ""

    disclaimer = " ⚠️ This is decision support only — not a medical diagnosis. Please consult a doctor."

    return (
        f"Hello {name}, I understand you're experiencing {symptom_phrase}, and we want to help you find care quickly."
        f"{likely_clause}{urgent_clause}{hospital_clause}{cost_clause}{financing_clause}{disclaimer}"
    )

def run_response_node(state: dict) -> dict:
    """
    Final node. Builds the structured assessment and packages frontend data.
    Packages everything into final JSON for frontend.
    """
    nodes_visited = state.get("nodes_visited", [])
    nodes_visited.append("response")

    cost_result   = state.get("cost_result", {})
    pfl_options   = state.get("pfl_options", {})
    loan_elig     = state.get("loan_eligibility", {})
    hospitals     = state.get("hospitals", [])
    provider_error = state.get("provider_error")
    clinical_signals = _clean_causes(state.get("possible_causes", []))
    explanation = _build_chat_recommendation(state)

    # ── Package final output for frontend ─────────────────────────────────────
    final_response = {
        # Meta
        "is_emergency":    state.get("is_emergency", False),
        "symptom_summary": state.get("symptom_summary", ""),
        "procedure":       state.get("procedure"),
        "icd10_code":      state.get("icd10_code"),
        "possible_causes": clinical_signals,
        "clinical_signals": clinical_signals,

        # AI explanation
        "explanation":     explanation,

        # Hospital cards (for frontend to render)
        "hospitals":       hospitals,
        "provider_error":  provider_error,

        # Cost breakdown (shown after hospital selected)
        "cost_result":     cost_result,
        "cost_results_by_hospital": state.get("cost_results_by_hospital", {}),

        # PFL financing
        "pfl_options":     pfl_options,
        "pfl_options_by_hospital": state.get("pfl_options_by_hospital", {}),

        # Loan eligibility
        "loan_eligibility": loan_elig,
        "loan_eligibility_by_hospital": state.get("loan_eligibility_by_hospital", {}),

        # Responsible AI
        "disclaimer":      None,
        "confidence":      cost_result.get("confidence") if cost_result else None,

        # Debug/logging
        "graph_path":      " → ".join(nodes_visited),
    }

    return {
        **state,
        "final_response": final_response,
        "nodes_visited":  nodes_visited,
    }
