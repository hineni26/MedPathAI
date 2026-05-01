import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-2.5-flash")

RESPONSE_PROMPT = """
You are MedPath AI, a warm and helpful Indian healthcare navigation assistant.
Write a brief, clear, empathetic response to show the user their results.

PATIENT INFO:
- Name: {name}
- Age: {age}
- City: {city}
- Comorbidities: {comorbidities}

QUERY INFO:
- Symptom/Query: {symptom_summary}
- Procedure: {procedure}
- Is Emergency: {is_emergency}
- Possible Causes: {possible_causes}

RESULTS:
- Hospitals found: {hospital_count}
- Top hospital: {top_hospital}
- Cost range: ₹{cost_min} – ₹{cost_max}
- Confidence: {confidence}%
- Loan eligibility: {loan_decision}
- Comorbidity warnings: {warnings}

Write a response with these sections in order:
1. One empathetic opening line acknowledging their situation (1 sentence)
2. If possible_causes exist — briefly mention the 2-3 likely causes (1-2 sentences)
3. One sentence about the hospitals found and cost range
4. If comorbidity warnings exist — mention them briefly
5. One sentence about PFL financing availability
6. End with the disclaimer: "⚠️ This is decision support only — not a medical diagnosis. Please consult a doctor."

RULES:
- Be warm but concise — max 5-6 sentences total
- Use simple English, no medical jargon
- Do NOT make up any numbers — use only what's provided above
- Do NOT suggest specific medications
- Address the user by name
- Return plain text only — no markdown, no bullet points
"""

def run_response_node(state: dict) -> dict:
    """
    Final node. Calls Gemini to write human-readable explanation.
    Packages everything into final JSON for frontend.
    """
    nodes_visited = state.get("nodes_visited", [])
    nodes_visited.append("response")

    profile       = state.get("user_profile", {})
    cost_result   = state.get("cost_result", {})
    pfl_options   = state.get("pfl_options", {})
    loan_elig     = state.get("loan_eligibility", {})
    hospitals     = state.get("hospitals", [])
    is_emergency  = state.get("is_emergency", False)

    top_hospital  = hospitals[0]["hospital_name"] if hospitals else "N/A"
    cost_min      = f"{cost_result.get('total_min', 0):,}" if cost_result else "N/A"
    cost_max      = f"{cost_result.get('total_max', 0):,}" if cost_result else "N/A"
    confidence    = int(cost_result.get("confidence", 0) * 100) if cost_result else 0
    warnings      = ", ".join(cost_result.get("comorbidity_warnings", [])) if cost_result else "none"

    # ── Generate explanation via Gemini ───────────────────────────────────────
    try:
        prompt = RESPONSE_PROMPT.format(
            name           = profile.get("name", "there"),
            age            = profile.get("age", "unknown"),
            city           = state.get("city", profile.get("city", "your city")),
            comorbidities  = ", ".join(profile.get("comorbidities", [])) or "none",
            symptom_summary= state.get("symptom_summary", state.get("user_input", "")),
            procedure      = state.get("procedure", "the procedure"),
            is_emergency   = is_emergency,
            possible_causes= ", ".join(state.get("possible_causes", [])) or "not determined",
            hospital_count = len(hospitals),
            top_hospital   = top_hospital,
            cost_min       = cost_min,
            cost_max       = cost_max,
            confidence     = confidence,
            loan_decision  = loan_elig.get("decision", "UNKNOWN") if loan_elig else "UNKNOWN",
            warnings       = warnings or "none",
        )

        response    = model.generate_content(prompt)
        explanation = response.text.strip()

    except Exception as e:
        print(f"❌ response_node Gemini error: {e}")
        explanation = (
            f"Hi {profile.get('name', 'there')}! "
            f"I found {len(hospitals)} hospitals for you. "
            f"Estimated cost: ₹{cost_min} – ₹{cost_max}. "
            f"⚠️ This is decision support only — not a medical diagnosis. Please consult a doctor."
        )

    # ── Package final output for frontend ─────────────────────────────────────
    final_response = {
        # Meta
        "is_emergency":    is_emergency,
        "symptom_summary": state.get("symptom_summary", ""),
        "procedure":       state.get("procedure"),
        "icd10_code":      state.get("icd10_code"),
        "possible_causes": state.get("possible_causes", []),

        # AI explanation
        "explanation":     explanation,

        # Hospital cards (for frontend to render)
        "hospitals":       hospitals,

        # Cost breakdown (shown after hospital selected)
        "cost_result":     cost_result,

        # PFL financing
        "pfl_options":     pfl_options,

        # Loan eligibility
        "loan_eligibility": loan_elig,

        # Responsible AI
        "disclaimer":      "⚠️ This is decision support only — not a medical diagnosis. Costs are estimates and may vary. Please consult a qualified doctor before making medical decisions.",
        "confidence":      cost_result.get("confidence") if cost_result else None,

        # Debug/logging
        "graph_path":      " → ".join(nodes_visited),
    }

    return {
        **state,
        "final_response": final_response,
        "nodes_visited":  nodes_visited,
    }