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
6. If your clinical signal/condition maps to a supported procedure, fill the procedure field. For example, appendicitis maps to appendectomy.
7. Do not repeat a clarification question already asked in the conversation history. Ask the next most useful missing detail instead.
8. Return ONLY the JSON. No explanation. No markdown. No preamble.
"""

def _normalize_question(text: str | None) -> str:
    return " ".join((text or "").strip().lower().split())


def _question_was_asked(question: str | None, history: list) -> bool:
    normalized_question = _normalize_question(question)
    if not normalized_question:
        return False

    for turn in history:
        assistant_text = _normalize_question(turn.get("assistant"))
        if normalized_question and normalized_question in assistant_text:
            return True
    return False


def run_intent_node(state: dict) -> dict:
    user_input    = state.get("user_input", "")
    profile       = state.get("user_profile", {})
    history       = state.get("conversation_history", [])
    nodes_visited = state.get("nodes_visited", [])
    nodes_visited.append("intent")

    history_str = ""
    if history:
        for turn in history[-6:]:
            history_str += f"User: {turn.get('user', '')}\n"
            history_str += f"MedPath: {turn.get('assistant', '')}\n"
    else:
        history_str = "None — this is the first message"

    prompt = INTENT_PROMPT.format(
        procedures    = ", ".join(SUPPORTED_PROCEDURES),
        user_input    = user_input,
        name          = profile.get("name", "User"),
        age           = profile.get("age", "unknown"),
        city          = profile.get("city", "unknown"),
        comorbidities = ", ".join(profile.get("comorbidities", [])) or "none",
        history       = history_str,
    )

    try:
        response  = model.generate_content(prompt)
        raw       = response.text.strip()

        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.strip()

        extracted = json.loads(raw)

    except Exception as e:
        print(f"❌ intent_node Gemini error: {e}")
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

    lower_input = user_input.lower()
    if any(kw in lower_input for kw in EMERGENCY_KEYWORDS):
        extracted["is_emergency"] = True
        extracted["ambiguity_score"] = min(extracted.get("ambiguity_score", 0), 0.3)

    if extracted.get("is_emergency"):
        extracted["ambiguity_score"] = 0.1
        extracted["clarifying_question"] = None

    procedure = extracted.get("procedure")
    if procedure not in SUPPORTED_PROCEDURES:
        procedure = None

    ambiguity_score = extracted.get("ambiguity_score", 0.5)
    try:
        ambiguity_score = float(ambiguity_score)
    except (TypeError, ValueError):
        ambiguity_score = 0.5

    clarifying_question = extracted.get("clarifying_question")
    if _question_was_asked(clarifying_question, history):
        clarifying_question = (
            "What other symptoms, timing, severity, or changes have you noticed since this started?"
        )

    if procedure:
        ambiguity_score = min(ambiguity_score, 0.25)
        clarifying_question = None

    is_emergency = extracted.get("is_emergency", False)
    recommendation_ready = bool(
        procedure
        or is_emergency
        or (ambiguity_score <= 0.6 and not clarifying_question)
    )
    direct_procedure_request = bool(procedure and ambiguity_score < 0.3)
    emergency_confidence = 0.9 if is_emergency else 0.0

    return {
        **state,
        "procedure":           procedure,
        "city":                extracted.get("city") or profile.get("city"),
        "budget":              extracted.get("budget") or state.get("budget"),
        "deadline_days":       extracted.get("deadline_days"),
        "is_emergency":        is_emergency,
        "ambiguity_score":     ambiguity_score,
        "clarifying_question": clarifying_question,
        "possible_causes":     extracted.get("possible_causes", []),
        "icd10_code":          extracted.get("icd10_code"),
        "symptom_summary":     extracted.get("symptom_summary", user_input),
        "follow_up_answers":   extracted.get("follow_up_answers", {}),
        "recommendation_ready": recommendation_ready,
        "direct_procedure_request": direct_procedure_request,
        "emergency_confidence": emergency_confidence,
        "nodes_visited":       nodes_visited,
    }


def get_direct_procedure_intent(
    user_input: str,
    user_profile: dict,
    conversation_history: list | None = None,
    budget: int | None = None,
) -> dict | None:
    """
    Compatibility helper for main.py.
    Returns provider-ready intent only when Gemini maps the request to a
    supported procedure.
    """
    result = run_intent_node({
        "user_input": user_input,
        "user_profile": user_profile or {},
        "conversation_history": conversation_history or [],
        "budget": budget,
        "nodes_visited": [],
    })

    if result.get("procedure") not in SUPPORTED_PROCEDURES:
        return None

    return {
        "procedure": result.get("procedure"),
        "city": result.get("city"),
        "budget": result.get("budget"),
        "deadline_days": result.get("deadline_days"),
        "is_emergency": result.get("is_emergency", False),
        "ambiguity_score": min(result.get("ambiguity_score", 0.2), 0.2),
        "clarifying_question": None,
        "possible_causes": result.get("possible_causes", []),
        "icd10_code": result.get("icd10_code"),
        "symptom_summary": result.get("symptom_summary", user_input),
        "follow_up_answers": result.get("follow_up_answers", {}),
        "recommendation_ready": True,
        "direct_procedure_request": True,
        "emergency_confidence": 0.9 if result.get("is_emergency") else 0.0,
    }
