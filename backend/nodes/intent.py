import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-2.5-flash")

# ── Supported procedures (exactly as in your CSV) ──────────────────────────────
SUPPORTED_PROCEDURES = [
    "angioplasty", "appendectomy", "arthroscopy", "bypass_cabg",
    "c_section", "cataract", "colonoscopy", "ct_scan", "dialysis_single",
    "ecg_echo", "endoscopy", "gallbladder_surgery", "hernia_repair",
    "hip_replacement", "hysterectomy", "kidney_stone_removal",
    "knee_replacement", "lasik", "mri_scan", "normal_delivery"
]

# ── Emergency symptom keywords ─────────────────────────────────────────────────
EMERGENCY_KEYWORDS = [
    "chest pain", "heart attack", "stroke", "can't breathe",
    "cannot breathe", "difficulty breathing", "severe bleeding",
    "unconscious", "collapsed", "seizure", "paralysis",
    "crushing pain", "left arm pain", "jaw pain", "sudden numbness"
]

INTENT_PROMPT = """
You are a clinical intake AI for MedPath, an Indian healthcare navigation system.
Your job is to extract structured information from a user's health query.

SUPPORTED PROCEDURES (map user's words to exactly one of these):
{procedures}

USER QUERY: "{user_input}"

USER PROFILE (already known — do not ask for these again):
- Name: {name}
- Age: {age}
- City: {city}
- Comorbidities: {comorbidities}

CONVERSATION HISTORY:
{history}

Extract and return ONLY a valid JSON object with these fields:

{{
  "procedure": "<one of the supported procedures above, or null if unknown>",
  "city": "<city name, use profile city if not mentioned>",
  "budget": <integer in INR or null>,
  "deadline_days": <integer days from today or null>,
  "is_emergency": <true if symptoms suggest urgent/life-threatening, else false>,
  "ambiguity_score": <float 0.0-1.0, where >0.6 means clarification needed>,
  "clarifying_question": "<one focused question to ask if ambiguity_score > 0.6, else null>",
  "possible_causes": ["<medical condition 1>", "<medical condition 2>"],
  "icd10_code": "<ICD-10 code for most likely condition, or null>",
  "symptom_summary": "<1 sentence summary of what user described>",
  "follow_up_answers": {{
    "pain_type": "<if mentioned>",
    "pain_location": "<if mentioned>",
    "duration": "<if mentioned>",
    "additional_symptoms": ["<symptom1>", "<symptom2>"]
  }}
}}

RULES:
1. If user directly mentions a procedure or condition, set ambiguity_score < 0.3
2. If user only describes vague symptoms, set ambiguity_score > 0.6 and ask ONE clarifying question
3. If symptoms match emergency keywords (chest pain spreading to arm, difficulty breathing, stroke signs), set is_emergency = true
4. Always use the profile city if user does not mention a city
5. possible_causes should have 2-3 entries max
6. Return ONLY the JSON. No explanation. No markdown. No preamble.
"""

def run_intent_node(state: dict) -> dict:
    """
    Takes current state, calls Gemini to extract structured intent.
    Returns updated state.
    """
    user_input   = state.get("user_input", "")
    profile      = state.get("user_profile", {})
    history      = state.get("conversation_history", [])
    nodes_visited = state.get("nodes_visited", [])
    nodes_visited.append("intent")

    # Build history string for context
    history_str = ""
    if history:
        for turn in history[-6:]:  # last 3 exchanges
            history_str += f"User: {turn.get('user', '')}\n"
            history_str += f"MedPath: {turn.get('assistant', '')}\n"
    else:
        history_str = "None — this is the first message"

    prompt = INTENT_PROMPT.format(
        procedures   = ", ".join(SUPPORTED_PROCEDURES),
        user_input   = user_input,
        name         = profile.get("name", "User"),
        age          = profile.get("age", "unknown"),
        city         = profile.get("city", "unknown"),
        comorbidities= ", ".join(profile.get("comorbidities", [])) or "none",
        history      = history_str,
    )

    try:
        response = model.generate_content(prompt)
        raw = response.text.strip()

        # Strip markdown fences if Gemini adds them
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.strip()

        extracted = json.loads(raw)

    except Exception as e:
        print(f"❌ intent_node Gemini error: {e}")
        # Fallback — ask clarifying question
        extracted = {
            "procedure":           None,
            "city":                profile.get("city"),
            "budget":              None,
            "deadline_days":       None,
            "is_emergency":        False,
            "ambiguity_score":     0.9,
            "clarifying_question": "Could you tell me more about what you're experiencing or the procedure you need?",
            "possible_causes":     [],
            "icd10_code":          None,
            "symptom_summary":     user_input,
            "follow_up_answers":   {},
        }

    # Emergency override — check keywords even if Gemini missed it
    lower_input = user_input.lower()
    if any(kw in lower_input for kw in EMERGENCY_KEYWORDS):
        extracted["is_emergency"] = True
        extracted["ambiguity_score"] = min(extracted.get("ambiguity_score", 0), 0.3)

    # If emergency — don't ask clarifying questions, go straight to hospitals
    if extracted.get("is_emergency"):
        extracted["ambiguity_score"] = 0.1
        extracted["clarifying_question"] = None

    return {
        **state,
        "procedure":            extracted.get("procedure"),
        "city":                 extracted.get("city") or profile.get("city"),
        "budget":               extracted.get("budget") or state.get("budget"),
        "deadline_days":        extracted.get("deadline_days"),
        "is_emergency":         extracted.get("is_emergency", False),
        "ambiguity_score":      extracted.get("ambiguity_score", 0.5),
        "clarifying_question":  extracted.get("clarifying_question"),
        "possible_causes":      extracted.get("possible_causes", []),
        "icd10_code":           extracted.get("icd10_code"),
        "symptom_summary":      extracted.get("symptom_summary", user_input),
        "follow_up_answers":    extracted.get("follow_up_answers", {}),
        "nodes_visited":        nodes_visited,
    }