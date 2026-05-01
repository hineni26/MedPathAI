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
    "heart attack", "stroke", "can't breathe",
    "cannot breathe", "difficulty breathing", "severe bleeding",
    "unconscious", "collapsed", "seizure", "paralysis",
    "crushing pain", "left arm pain", "jaw pain", "sudden numbness",
    "worst headache", "sudden severe headache", "vision loss",
    "confusion", "fainted", "fainting"
]

HIGH_RISK_CHEST_PAIN_TERMS = [
    "arm", "left arm", "jaw", "back", "spreading", "radiating",
    "crushing", "walking", "walk", "climb", "stairs",
    "sweating", "breath", "nausea"
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

CURRENT CLINICAL CONTEXT:
{clinical_context}

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
  "recommendation_ready": <true only when enough symptom detail exists to show hospitals>,
  "emergency_confidence": <float 0.0-1.0 estimating confidence of immediate emergency>,
  "follow_up_answers": {{
    "pain_type": "<if mentioned>",
    "pain_location": "<if mentioned>",
    "duration": "<if mentioned>",
    "additional_symptoms": ["<symptom1>", "<symptom2>"]
  }}
}}

RULES:
1. If user directly mentions a procedure or condition, set ambiguity_score < 0.3
2. For unclear symptom-only queries, ask 1-2 concise follow-up questions. Do not ask more than 2 follow-ups before choosing the closest supported hospital-search route.
3. For chest pain alone on the first turn, recommendation_ready=false and is_emergency=false. Ask about pain type, radiation to arm/jaw/back, exertion, duration, breathlessness, sweating, and nausea.
4. Set is_emergency=true only when red flags are present with high confidence, such as chest tightness/pressure radiating to arm/jaw/back, worse on exertion, severe breathing trouble, stroke signs, collapse, or uncontrolled bleeding.
5. If is_emergency=true, set emergency_confidence >= 0.85. Otherwise keep emergency_confidence below 0.85.
6. Set recommendation_ready=true when either the user asks for a specific procedure/hospital search, or follow-up answers provide enough severity/context to identify likely causes and urgency.
7. Always use the profile city if user does not mention a city
8. possible_causes should have 2-3 entries max
9. If symptoms mention kidney/flank/back-side pain with peeing/urination/urine/blood/burning, map to kidney_stone_removal unless a better supported procedure is directly named.
10. If symptoms mention headache/head pain with nausea, throbbing, light/noise sensitivity, focus trouble, dizziness, or back-of-head pain, map to mri_scan as a diagnostic hospital-search fallback unless emergency red flags require ct_scan.
11. These possible_causes are internal routing hints. Do not write them as a diagnosis for the user.
12. Return ONLY the JSON. No explanation. No markdown. No preamble.
"""

URINARY_PAIN_TERMS = [
    "kidney", "flank", "side pain", "back pain", "lower back",
    "pee", "peeing", "urinate", "urinating", "urination", "urine",
    "burning", "blood in urine"
]

HEADACHE_TERMS = [
    "headache", "headaches", "head pain", "migraine", "back of the head",
    "back of head", "occipital", "throbbing", "sensitive to light",
    "sensitivity to light", "sensitive to noise", "light and noise",
    "nausea", "nauseous", "dizzy", "dizziness", "not able to focus",
    "unable to focus", "blurred vision"
]

HEADACHE_RED_FLAGS = [
    "worst headache", "sudden severe headache", "sudden headache",
    "weakness", "numbness", "slurred speech", "confusion",
    "vision loss", "fainted", "fainting", "seizure", "stiff neck",
    "high fever"
]

CHEST_TERMS = [
    "chest pain", "chest tightness", "chest pressure", "heart pain",
    "palpitations", "shortness of breath", "breathless", "breathlessness",
    "difficulty breathing"
]

ABDOMINAL_TERMS = [
    "stomach ache", "stomach pain", "abdominal pain", "abdomen pain", "belly pain",
    "tummy ache", "tummy pain",
    "right lower abdomen", "lower right abdomen", "right upper abdomen",
    "bottom right", "bottom right side", "right bottom", "right lower",
    "upper abdomen", "acidity", "acid reflux", "heartburn", "gastric",
    "vomiting", "nausea", "bloating", "indigestion", "difficulty swallowing",
    "gallbladder", "gall stone", "gallstone"
]

RESPIRATORY_TERMS = [
    "cough", "cold", "wheezing", "breathing problem", "shortness of breath",
    "breathless", "sore throat", "throat pain", "runny nose", "blocked nose",
    "sinus", "phlegm"
]

SKIN_TERMS = [
    "rash", "itching", "itchy", "hives", "skin allergy", "boil",
    "red patches", "swelling on skin", "burn", "wound", "cut"
]

EAR_NOSE_THROAT_TERMS = [
    "ear pain", "earache", "hearing loss", "ringing", "vertigo",
    "nose bleed", "nosebleed", "throat pain", "sore throat", "tonsil"
]

DENTAL_TERMS = [
    "tooth pain", "toothache", "gum pain", "jaw swelling", "dental pain",
    "bleeding gums"
]

NEURO_TERMS = [
    "dizzy", "dizziness", "faint", "fainting", "numbness", "tingling",
    "weakness", "confusion", "seizure"
]

GENERAL_BODY_TERMS = [
    "body pain", "body ache", "fatigue", "weakness", "tired",
    "weight loss", "lump", "swelling", "pain"
]

BOWEL_TERMS = [
    "blood in stool", "rectal bleeding", "black stool", "colon",
    "bowel", "constipation", "persistent diarrhea", "diarrhoea",
    "colonoscopy"
]

ORTHO_TERMS = [
    "knee pain", "knee injury", "knee swelling", "hip pain", "hip fracture",
    "joint pain", "shoulder pain", "back pain", "neck pain", "ankle pain",
    "wrist pain", "sports injury", "ligament", "meniscus", "arthritis",
    "can't walk", "cannot walk"
]

EYE_TERMS = [
    "blurry vision", "blurred vision", "cloudy vision", "cataract",
    "poor vision", "eye pain", "vision correction", "remove specs",
    "remove glasses", "lasik"
]

PREGNANCY_TERMS = [
    "pregnant", "pregnancy", "labour", "labor", "delivery",
    "water broke", "contractions", "c section", "c-section", "cesarean"
]

GYNEC_TERMS = [
    "heavy periods", "heavy bleeding", "fibroid", "fibroids", "uterus",
    "uterine", "pelvic pain", "hysterectomy"
]

KIDNEY_DISEASE_TERMS = [
    "kidney failure", "renal failure", "dialysis", "high creatinine",
    "creatinine", "low urine output"
]

GENERAL_DIAGNOSTIC_TERMS = [
    "severe pain", "swelling", "lump", "injury", "fall",
    "accident", "scan", "xray", "x-ray", "diagnosis", "not able to focus"
]

FEVER_TERMS = [
    "fever", "high fever", "very high fever", "temperature", "temp",
    "chills", "body ache", "body aches"
]

FEVER_EMERGENCY_TERMS = [
    "confusion", "fainting", "fainted", "seizure", "stiff neck",
    "difficulty breathing", "cannot breathe", "can't breathe",
    "blue lips", "severe dehydration", "not passing urine",
    "unconscious", "rash that does not fade"
]

DIRECT_PROCEDURE_TERMS = [
    *SUPPORTED_PROCEDURES,
    "angioplasty", "appendix surgery", "appendectomy", "arthroscopy",
    "bypass", "cabg", "c section", "c-section", "cataract surgery",
    "colonoscopy", "ct scan", "dialysis", "ecg", "echo", "endoscopy",
    "gallbladder surgery", "hernia repair", "hip replacement",
    "hysterectomy", "kidney stone removal", "knee replacement",
    "lasik", "mri", "mri scan", "normal delivery"
]

FIRST_TURN_CLARIFICATION_RULES = [
    {
        "terms": ABDOMINAL_TERMS,
        "detail_terms": [
            "bottom right", "bottom right side", "right lower", "right side",
            "left side", "upper", "lower", "vomiting", "nausea", "fever",
            "diarrhea", "diarrhoea", "blood", "severe"
        ],
        "question": "Can you tell me where exactly in your stomach you're feeling the pain, and if you have any other symptoms like nausea or fever?",
        "signals": ["Indigestion", "Gas", "Mild food poisoning"],
        "summary": "Stomach or abdominal discomfort without enough location or symptom detail.",
    },
    {
        "terms": CHEST_TERMS,
        "detail_terms": HIGH_RISK_CHEST_PAIN_TERMS + ["sharp", "burning", "tight", "pressure", "duration"],
        "question": "Can you describe the chest symptom: is it sharp, burning, tight, or pressure-like, and does it spread to your arm, jaw, back, or come with sweating or breathlessness?",
        "signals": ["Acidity or reflux", "Muscle strain", "Cardiac warning sign"],
        "summary": "Chest symptoms without enough severity or radiation detail.",
    },
    {
        "terms": HEADACHE_TERMS,
        "detail_terms": HEADACHE_RED_FLAGS + ["nausea", "vomiting", "light", "noise", "vision", "throbbing", "one side"],
        "question": "Where is the headache, how severe is it, and do you have nausea, vomiting, vision changes, dizziness, weakness, or sensitivity to light?",
        "signals": ["Migraine", "Tension headache", "Sinus headache"],
        "summary": "Headache symptoms without enough severity or associated symptom detail.",
    },
    {
        "terms": FEVER_TERMS,
        "detail_terms": ["cough", "rash", "headache", "neck", "breathing", "vomiting", "urination", "temperature"],
        "question": "How long has the fever been there, what is your temperature, and do you also have cough, rash, severe headache, neck stiffness, vomiting, breathing trouble, or burning urination?",
        "signals": ["Viral infection", "Flu-like illness", "Dengue or other infection"],
        "summary": "Fever without enough duration or associated symptom detail.",
    },
    {
        "terms": RESPIRATORY_TERMS,
        "detail_terms": ["fever", "wheezing", "blood", "breathless", "chest pain", "phlegm", "duration"],
        "question": "How long have you had the cough or breathing symptom, and do you have fever, wheezing, chest pain, blood in phlegm, or shortness of breath?",
        "signals": ["Common cold", "Bronchitis", "Asthma or allergy flare"],
        "summary": "Respiratory symptoms without enough duration or red-flag detail.",
    },
    {
        "terms": URINARY_PAIN_TERMS,
        "detail_terms": ["burning", "blood", "fever", "flank", "kidney", "lower back", "vomiting"],
        "question": "Is there burning while urinating, blood in urine, fever, vomiting, or pain in your side or lower back?",
        "signals": ["Urinary tract infection", "Kidney stone", "Kidney infection"],
        "summary": "Urinary or side-pain symptoms without enough associated symptom detail.",
    },
    {
        "terms": ORTHO_TERMS + ["back pain", "neck pain", "shoulder pain", "ankle pain", "wrist pain"],
        "detail_terms": ["injury", "fall", "swelling", "can't walk", "cannot walk", "numbness", "weakness", "severe"],
        "question": "Which joint or area hurts, did it start after an injury or fall, and is there swelling, numbness, weakness, or trouble walking?",
        "signals": ["Muscle strain", "Ligament injury", "Arthritis flare"],
        "summary": "Bone, joint, or muscle pain without enough injury or severity detail.",
    },
    {
        "terms": SKIN_TERMS,
        "detail_terms": ["fever", "painful", "spreading", "pus", "burn", "allergy", "new medicine"],
        "question": "Where is the skin problem, is it itchy or painful, and is it spreading or associated with fever, pus, allergy, burn, or a new medicine?",
        "signals": ["Skin allergy", "Infection", "Inflammation"],
        "summary": "Skin symptoms without enough spread or infection detail.",
    },
    {
        "terms": EYE_TERMS,
        "detail_terms": ["pain", "red", "vision loss", "blurred", "injury", "cloudy", "discharge"],
        "question": "Is the eye problem in one or both eyes, and do you have pain, redness, discharge, injury, cloudy vision, or sudden vision loss?",
        "signals": ["Eye strain", "Conjunctivitis", "Cataract or vision issue"],
        "summary": "Eye symptoms without enough vision or pain detail.",
    },
    {
        "terms": EAR_NOSE_THROAT_TERMS,
        "detail_terms": ["fever", "hearing", "discharge", "swelling", "breathing", "difficulty swallowing", "dizziness"],
        "question": "How long has the ear, nose, or throat symptom been there, and do you have fever, discharge, hearing change, dizziness, swelling, or trouble swallowing?",
        "signals": ["Throat infection", "Ear infection", "Sinus congestion"],
        "summary": "Ear, nose, or throat symptoms without enough associated symptom detail.",
    },
    {
        "terms": DENTAL_TERMS,
        "detail_terms": ["swelling", "fever", "bleeding", "injury", "severe", "pus"],
        "question": "Which tooth or gum area hurts, and is there swelling, fever, bleeding, injury, pus, or severe pain while chewing?",
        "signals": ["Dental infection", "Gum inflammation", "Tooth decay"],
        "summary": "Dental symptoms without enough swelling or infection detail.",
    },
    {
        "terms": GYNEC_TERMS,
        "detail_terms": ["pregnant", "heavy", "severe", "fever", "bleeding", "pelvic", "duration"],
        "question": "Can you tell me how long this has been happening, whether bleeding is heavy, and if there is pelvic pain, fever, pregnancy, or dizziness?",
        "signals": ["Hormonal bleeding", "Fibroid-related symptoms", "Pelvic infection screen"],
        "summary": "Gynecologic symptoms without enough bleeding or pelvic symptom detail.",
    },
    {
        "terms": PREGNANCY_TERMS,
        "detail_terms": ["contractions", "water broke", "bleeding", "pain", "baby movement", "previous c section"],
        "question": "How many weeks pregnant are you, and do you have contractions, water leakage, bleeding, severe pain, reduced baby movement, or a previous C-section?",
        "signals": ["Delivery planning", "Pregnancy checkup need", "Obstetric warning sign"],
        "summary": "Pregnancy-related concern without enough urgency or delivery detail.",
    },
    {
        "terms": GENERAL_BODY_TERMS,
        "detail_terms": ["fever", "injury", "fall", "severe", "sudden", "weight loss", "night sweats", "lump", "swelling"],
        "question": "Where exactly is the symptom, how long has it been happening, and is there fever, injury, swelling, sudden weakness, weight loss, or severe pain?",
        "signals": ["Infection or inflammation", "Muscle strain", "General medical evaluation"],
        "summary": "General body symptoms without enough location or severity detail.",
    },
]

def _combined_user_context(user_input: str, history: list) -> str:
    previous_user_text = " ".join(
        turn.get("user", "")
        for turn in history[-4:]
    )
    return f"{previous_user_text} {user_input}".strip()


def _contains_any(text: str, terms: list[str]) -> bool:
    return any(term in text for term in terms)


def _mentions_supported_procedure(text: str) -> bool:
    normalized = text.replace("-", " ")
    return any(term.replace("_", " ") in normalized for term in DIRECT_PROCEDURE_TERMS)


def _set_fallback(
    extracted: dict,
    procedure: str,
    causes: list[str],
    summary: str,
    icd10_code: str | None = None,
    is_emergency: bool = False,
    emergency_confidence: float = 0.0,
) -> None:
    extracted.update({
        "procedure": procedure,
        "ambiguity_score": 0.3,
        "clarifying_question": None,
        "possible_causes": (extracted.get("possible_causes") or causes)[:3],
        "icd10_code": extracted.get("icd10_code") or icd10_code,
        "symptom_summary": extracted.get("symptom_summary") or summary,
        "recommendation_ready": True,
    })

    if is_emergency:
        extracted["is_emergency"] = True
        extracted["emergency_confidence"] = max(
            extracted.get("emergency_confidence", 0) or 0,
            emergency_confidence,
        )


def _set_clarification(
    extracted: dict,
    question: str,
    summary: str,
    causes: list[str] | None = None,
) -> None:
    extracted.update({
        "procedure": None,
        "ambiguity_score": 0.9,
        "clarifying_question": question,
        "symptom_summary": extracted.get("symptom_summary") or summary,
        "recommendation_ready": False,
        "is_emergency": False,
        "emergency_confidence": 0.0,
    })
    if causes is not None:
        extracted["possible_causes"] = causes[:3]


def _first_turn_clarification_rule(text: str) -> dict | None:
    if _mentions_supported_procedure(text):
        return None

    if _contains_any(text, EMERGENCY_KEYWORDS) or _contains_any(text, FEVER_EMERGENCY_TERMS):
        return None

    for rule in FIRST_TURN_CLARIFICATION_RULES:
        if not _contains_any(text, rule["terms"]):
            continue
        if _contains_any(text, rule["detail_terms"]):
            continue
        return rule

    return None


def _apply_symptom_fallbacks(extracted: dict, context_text: str, clarify_attempts: int) -> dict:
    """
    Map common symptom language to the closest procedure this demo database supports.
    This keeps the chat decisive after one short follow-up.
    """
    lower_context = context_text.lower()
    mapped = bool(extracted.get("procedure") and extracted.get("recommendation_ready"))

    if clarify_attempts == 0:
        clarification_rule = _first_turn_clarification_rule(lower_context)
        if clarification_rule:
            _set_clarification(
                extracted,
                question=clarification_rule["question"],
                summary=clarification_rule["summary"],
                causes=clarification_rule["signals"],
            )
            return extracted

    has_fever_context = _contains_any(lower_context, FEVER_TERMS)
    has_fever_emergency = has_fever_context and _contains_any(lower_context, FEVER_EMERGENCY_TERMS)

    if has_fever_emergency:
        _set_fallback(
            extracted,
            procedure="ct_scan",
            causes=[
                "fever with emergency warning signs",
                "serious infection screen",
                "urgent clinical evaluation",
            ],
            summary="High fever with emergency warning signs.",
            icd10_code="R50.9",
            is_emergency=True,
            emergency_confidence=0.9,
        )
        mapped = True

    has_urinary_context = any(term in lower_context for term in URINARY_PAIN_TERMS)
    has_kidney_or_flank_pain = any(
        term in lower_context
        for term in ["kidney", "flank", "side pain", "back pain", "lower back"]
    )
    has_urination_symptom = any(
        term in lower_context
        for term in ["pee", "peeing", "urinate", "urinating", "urination", "urine", "burning", "blood"]
    )

    should_map_urinary = (
        (has_kidney_or_flank_pain and has_urination_symptom)
        or "kidney stone" in lower_context
        or (clarify_attempts >= 1 and has_urinary_context)
    )

    if should_map_urinary:
        extracted["possible_causes"] = [
            "Kidney stone",
            "Urinary tract infection",
            "Kidney infection",
        ]
        _set_fallback(
            extracted,
            procedure="kidney_stone_removal",
            causes=extracted["possible_causes"],
            summary="Kidney or flank-area pain with urination symptoms.",
            icd10_code="N20",
        )
        mapped = True

    has_headache_context = any(term in lower_context for term in HEADACHE_TERMS)
    has_headache_anchor = any(
        term in lower_context
        for term in ["headache", "headaches", "head pain", "migraine", "back of the head", "back of head"]
    )
    has_headache_detail = any(
        term in lower_context
        for term in [
            "throbbing", "nausea", "nauseous", "sensitive to light",
            "sensitivity to light", "sensitive to noise", "light and noise",
            "not able to focus", "unable to focus", "dizzy", "dizziness",
            "blurred vision"
        ]
    )
    has_headache_red_flag = any(term in lower_context for term in HEADACHE_RED_FLAGS)

    if has_headache_context and (has_headache_anchor or has_headache_detail):
        extracted["possible_causes"] = [
            "Migraine-like headache",
            "Tension headache",
            "Neurological warning sign screen",
        ]
        _set_fallback(
            extracted,
            procedure="ct_scan" if has_headache_red_flag else "mri_scan",
            causes=extracted["possible_causes"],
            summary="Headache symptoms needing clinical evaluation.",
            icd10_code="R51",
            is_emergency=has_headache_red_flag,
            emergency_confidence=0.88,
        )
        mapped = True

    if not mapped and _contains_any(lower_context, CHEST_TERMS):
        high_risk = _contains_any(lower_context, HIGH_RISK_CHEST_PAIN_TERMS)
        extracted["possible_causes"] = [
            "Cardiac symptom screen",
            "Lung or breathing-related cause",
            "Reflux or muscle-related chest pain",
        ]
        _set_fallback(
            extracted,
            procedure="angioplasty" if high_risk else "ecg_echo",
            causes=extracted["possible_causes"],
            summary="Chest or breathing symptoms needing clinical evaluation.",
            icd10_code="R07.9",
            is_emergency=high_risk,
            emergency_confidence=0.9 if high_risk else 0.0,
        )
        mapped = True

    if not mapped and _contains_any(lower_context, RESPIRATORY_TERMS):
        extracted["possible_causes"] = [
            "Respiratory infection",
            "Asthma or allergy flare",
            "Bronchitis",
        ]
        _set_fallback(
            extracted,
            procedure="ct_scan",
            causes=extracted["possible_causes"],
            summary="Cough or breathing symptoms needing clinical evaluation.",
            icd10_code="R05",
            is_emergency=_contains_any(lower_context, ["can't breathe", "cannot breathe", "severe breathless"]),
            emergency_confidence=0.9,
        )
        mapped = True

    if not mapped and _contains_any(lower_context, KIDNEY_DISEASE_TERMS):
        _set_fallback(
            extracted,
            procedure="dialysis_single",
            causes=[
                "kidney function concern",
                "fluid or electrolyte issue",
                "renal care need",
            ],
            summary="Kidney function symptoms needing clinical evaluation.",
            icd10_code="N19",
        )
        mapped = True

    if not mapped and _contains_any(lower_context, BOWEL_TERMS):
        extracted["possible_causes"] = [
            "Bowel inflammation",
            "Intestinal infection",
            "Lower digestive tract concern",
        ]
        _set_fallback(
            extracted,
            procedure="colonoscopy",
            causes=extracted["possible_causes"],
            summary="Bowel or stool symptoms needing clinical evaluation.",
            icd10_code="K92.2",
        )
        mapped = True

    if not mapped and _contains_any(lower_context, ABDOMINAL_TERMS):
        if _contains_any(lower_context, ["gallbladder", "gall stone", "gallstone", "right upper abdomen"]):
            procedure = "gallbladder_surgery"
            causes = ["Gallbladder-related pain", "Gastritis", "Digestive tract concern"]
            icd10_code = "K80"
            summary = "Upper or right-sided abdominal pain needing clinical evaluation."
        elif _contains_any(
            lower_context,
            [
                "right lower abdomen", "lower right abdomen", "appendix",
                "bottom right", "bottom right side", "right bottom", "right lower",
            ],
        ):
            procedure = "appendectomy"
            causes = ["Appendicitis", "Irritable Bowel Syndrome (IBS)", "Gas or indigestion"]
            icd10_code = "K35"
            summary = "Pain in the bottom right side of the stomach."
        elif _contains_any(lower_context, ["acidity", "acid reflux", "heartburn", "gastric", "difficulty swallowing", "indigestion"]):
            procedure = "endoscopy"
            causes = ["Acid reflux", "Gastritis", "Indigestion"]
            icd10_code = "K30"
            summary = "Upper digestive symptoms needing clinical evaluation."
        else:
            procedure = "ct_scan"
            causes = ["Indigestion", "Gas", "Abdominal infection or inflammation"]
            icd10_code = "R10.9"
            summary = "Abdominal or digestive symptoms needing clinical evaluation."

        extracted["possible_causes"] = causes
        extracted["symptom_summary"] = summary
        _set_fallback(
            extracted,
            procedure=procedure,
            causes=causes,
            summary=summary,
            icd10_code=icd10_code,
        )
        mapped = True

    if not mapped and _contains_any(lower_context, EYE_TERMS):
        wants_vision_correction = _contains_any(
            lower_context,
            ["vision correction", "remove specs", "remove glasses", "lasik"]
        )
        cloudy_or_cataract = _contains_any(
            lower_context,
            ["cloudy vision", "cataract", "poor vision"]
        )
        extracted["possible_causes"] = [
            "Eye strain",
            "Conjunctivitis",
            "Cataract or vision issue",
        ]
        _set_fallback(
            extracted,
            procedure="lasik" if wants_vision_correction and not cloudy_or_cataract else "cataract",
            causes=extracted["possible_causes"],
            summary="Eye or vision symptoms needing clinical evaluation.",
            icd10_code="H53.9",
        )
        mapped = True

    if not mapped and _contains_any(lower_context, SKIN_TERMS):
        extracted["possible_causes"] = [
            "Skin allergy",
            "Skin infection",
            "Inflammation",
        ]
        _set_fallback(
            extracted,
            procedure="ct_scan",
            causes=extracted["possible_causes"],
            summary="Skin symptoms needing clinical evaluation.",
            icd10_code="R21",
        )
        mapped = True

    if not mapped and _contains_any(lower_context, EAR_NOSE_THROAT_TERMS):
        extracted["possible_causes"] = [
            "Throat infection",
            "Ear infection",
            "Sinus congestion",
        ]
        _set_fallback(
            extracted,
            procedure="ct_scan",
            causes=extracted["possible_causes"],
            summary="Ear, nose, or throat symptoms needing clinical evaluation.",
            icd10_code="H92.0",
        )
        mapped = True

    if not mapped and _contains_any(lower_context, DENTAL_TERMS):
        extracted["possible_causes"] = [
            "Dental infection",
            "Gum inflammation",
            "Tooth decay",
        ]
        _set_fallback(
            extracted,
            procedure="ct_scan",
            causes=extracted["possible_causes"],
            summary="Dental pain or gum symptoms needing clinical evaluation.",
            icd10_code="K08.8",
        )
        mapped = True

    if not mapped and _contains_any(lower_context, NEURO_TERMS):
        extracted["possible_causes"] = [
            "Neurological symptom screen",
            "Inner ear balance issue",
            "Metabolic or infection-related weakness",
        ]
        _set_fallback(
            extracted,
            procedure="ct_scan",
            causes=extracted["possible_causes"],
            summary="Dizziness, weakness, numbness, or neurological symptoms needing clinical evaluation.",
            icd10_code="R42",
            is_emergency=_contains_any(lower_context, ["confusion", "seizure", "sudden weakness", "fainting"]),
            emergency_confidence=0.88,
        )
        mapped = True

    if not mapped and _contains_any(lower_context, ORTHO_TERMS):
        if _contains_any(lower_context, ["hip pain", "hip fracture"]):
            procedure = "hip_replacement"
            causes = ["Hip joint concern", "Fracture or arthritis screen", "Mobility issue"]
        elif _contains_any(lower_context, ["arthritis", "can't walk", "cannot walk"]) and "knee" in lower_context:
            procedure = "knee_replacement"
            causes = ["Knee arthritis flare", "Joint degeneration", "Mobility issue"]
        else:
            procedure = "arthroscopy"
            causes = ["Joint injury", "Ligament or cartilage concern", "Orthopedic evaluation need"]

        extracted["possible_causes"] = causes
        _set_fallback(
            extracted,
            procedure=procedure,
            causes=causes,
            summary="Bone, joint, or injury symptoms needing clinical evaluation.",
            icd10_code="M25.5",
        )
        mapped = True

    if not mapped and _contains_any(lower_context, PREGNANCY_TERMS):
        needs_c_section = _contains_any(lower_context, ["c section", "c-section", "cesarean", "previous c section"])
        extracted["possible_causes"] = [
            "Pregnancy care need",
            "Delivery planning",
            "Obstetric evaluation need",
        ]
        _set_fallback(
            extracted,
            procedure="c_section" if needs_c_section else "normal_delivery",
            causes=extracted["possible_causes"],
            summary="Pregnancy or delivery symptoms needing clinical evaluation.",
            icd10_code="Z34",
        )
        mapped = True

    if not mapped and _contains_any(lower_context, GYNEC_TERMS):
        extracted["possible_causes"] = [
            "Gynecologic symptom evaluation",
            "Fibroid-related symptoms",
            "Pelvic or bleeding pattern concern",
        ]
        _set_fallback(
            extracted,
            procedure="hysterectomy",
            causes=extracted["possible_causes"],
            summary="Gynecologic symptoms needing clinical evaluation.",
            icd10_code="N93.9",
        )
        mapped = True

    if not mapped and _contains_any(lower_context, ["hernia", "groin swelling", "bulge in groin", "abdominal bulge"]):
        _set_fallback(
            extracted,
            procedure="hernia_repair",
            causes=[
                "hernia-like swelling",
                "abdominal wall concern",
                "groin swelling evaluation",
            ],
            summary="Swelling or bulge symptoms needing clinical evaluation.",
            icd10_code="K46",
        )
        mapped = True

    if has_fever_context and not mapped and clarify_attempts < 2:
        question = (
            "How long has the fever been there, and do you also have cough, rash, severe headache, neck stiffness, breathing trouble, vomiting, or burning urination?"
            if clarify_attempts == 0
            else "What is your temperature, and is there any confusion, breathing trouble, stiff neck, rash, dehydration, or severe weakness?"
        )
        _set_clarification(
            extracted,
            question=question,
            summary="High fever with unclear associated symptoms.",
            causes=["Viral infection", "Flu-like illness", "Dengue or other infection"],
        )
        return extracted

    if not mapped and (clarify_attempts >= 2 or _contains_any(lower_context, GENERAL_DIAGNOSTIC_TERMS)):
        _set_fallback(
            extracted,
            procedure="ct_scan",
            causes=[
                "general diagnostic evaluation",
                "pain or symptom source unclear",
                "doctor assessment needed",
            ],
            summary="Symptoms needing clinical evaluation.",
            icd10_code="R52",
        )

    if clarify_attempts >= 1 and extracted.get("procedure"):
        extracted["recommendation_ready"] = True
        extracted["clarifying_question"] = None
        extracted["ambiguity_score"] = min(extracted.get("ambiguity_score", 0.5) or 0.5, 0.5)

    return extracted

def run_intent_node(state: dict) -> dict:
    """
    Takes current state, calls Gemini to extract structured intent.
    Returns updated state.
    """
    user_input   = state.get("user_input", "")
    profile      = state.get("user_profile", {})
    history      = state.get("conversation_history", [])
    clarify_attempts = state.get("clarify_attempts", 0)
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

    clinical_context = _combined_user_context(user_input, history)

    prompt = INTENT_PROMPT.format(
        procedures   = ", ".join(SUPPORTED_PROCEDURES),
        user_input   = user_input,
        name         = profile.get("name", "User"),
        age          = profile.get("age", "unknown"),
        city         = profile.get("city", "unknown"),
        comorbidities= ", ".join(profile.get("comorbidities", [])) or "none",
        history      = history_str,
        clinical_context = clinical_context,
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
            "recommendation_ready": False,
            "emergency_confidence": 0.0,
            "follow_up_answers":   {},
        }

    extracted = _apply_symptom_fallbacks(extracted, clinical_context, clarify_attempts)

    # Emergency override — check keywords even if Gemini missed it
    lower_input = user_input.lower()
    history_text = " ".join(
        turn.get("user", "")
        for turn in history[-4:]
    ).lower()
    context_text = f"{history_text} {lower_input}"
    has_chest_pain = "chest pain" in context_text or "chest tightness" in context_text
    high_risk_chest = has_chest_pain and any(term in context_text for term in HIGH_RISK_CHEST_PAIN_TERMS)

    if any(kw in lower_input for kw in EMERGENCY_KEYWORDS) or high_risk_chest:
        extracted["is_emergency"] = True
        extracted["emergency_confidence"] = max(extracted.get("emergency_confidence", 0) or 0, 0.9)
        extracted["ambiguity_score"] = min(extracted.get("ambiguity_score", 0), 0.3)
        extracted["recommendation_ready"] = True

    # If emergency — don't ask clarifying questions, go straight to hospitals
    emergency_confidence = extracted.get("emergency_confidence", 0) or 0

    if extracted.get("is_emergency") and emergency_confidence >= 0.85:
        extracted["ambiguity_score"] = 0.1
        extracted["clarifying_question"] = None
        extracted["recommendation_ready"] = True

    if (
        "chest pain" in lower_input
        and not high_risk_chest
        and len(history) == 0
        and not extracted.get("procedure")
    ):
        extracted["is_emergency"] = False
        extracted["emergency_confidence"] = 0.4
        extracted["recommendation_ready"] = False
        extracted["ambiguity_score"] = 0.9
        extracted["clarifying_question"] = (
            "I'm sorry you're dealing with that. Chest pain can have several causes, so let me ask a few quick questions first. "
            "How would you describe the pain: sharp and stabbing, dull and pressure-like, burning, or tightness?"
        )

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
        "recommendation_ready": extracted.get("recommendation_ready", False),
        "emergency_confidence": extracted.get("emergency_confidence", 0),
        "follow_up_answers":    extracted.get("follow_up_answers", {}),
        "nodes_visited":        nodes_visited,
    }
