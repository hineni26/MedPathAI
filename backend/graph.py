from typing import TypedDict, Optional
from langgraph.graph import StateGraph, END

from nodes.intent   import run_intent_node
from nodes.provider import run_provider_node
from nodes.cost     import run_cost_node
from nodes.response import run_response_node

# ── MedState — shared state across all nodes ───────────────────────────────────
class MedState(TypedDict, total=False):
    # Input
    user_input:           str
    session_id:           str
    user_id:              str

    # GPS coordinates (passed from ChatRequest, used in provider_node)
    user_lat:             Optional[float]
    user_lon:             Optional[float]

    # User context (loaded from Supabase)
    user_profile:         dict
    user_financials:      dict

    # Conversation history (for multi-turn)
    conversation_history: list

    # Extracted by intent_node
    procedure:            Optional[str]
    city:                 Optional[str]
    budget:               Optional[int]
    deadline_days:        Optional[int]
    is_emergency:         bool
    ambiguity_score:      float
    clarifying_question:  Optional[str]
    possible_causes:      list
    icd10_code:           Optional[str]
    symptom_summary:      str
    follow_up_answers:    dict
    recommendation_ready: bool
    emergency_confidence: float

    # Set by provider_node
    hospitals:            list
    city_info:            Optional[dict]
    provider_error:       Optional[str]

    # Set after user selects hospital
    selected_hospital:    Optional[str]

    # Set by cost_node
    cost_result:          Optional[dict]
    pfl_options:          Optional[dict]
    loan_eligibility:     Optional[dict]
    loan_amount:          Optional[int]

    # Set by response_node
    final_response:       Optional[dict]

    # Debug
    nodes_visited:        list
    clarify_attempts:     int


# ── Routing logic ──────────────────────────────────────────────────────────────
def route_after_intent(state: MedState) -> str:
    """
    After intent_node:
    - If emergency           → skip clarification, go straight to provider
    - If ambiguity is high    → ask up to two focused clarifying questions
    - If procedure known     → go to provider
    """
    is_emergency     = state.get("is_emergency", False)
    emergency_conf   = state.get("emergency_confidence", 0.0)
    ready            = state.get("recommendation_ready", False)
    ambiguity_score  = state.get("ambiguity_score", 0.0)
    clarify_attempts = state.get("clarify_attempts", 0)

    if is_emergency and emergency_conf >= 0.85:
        return "provider"

    if (not ready or ambiguity_score > 0.7) and clarify_attempts < 2:
        return "clarify"

    return "provider"


def clarify_node(state: MedState) -> MedState:
    """
    Surfaces the clarifying question to the user.
    Increments clarify_attempts to prevent infinite loops.
    """
    attempts = state.get("clarify_attempts", 0)
    return {
        **state,
        "clarify_attempts": attempts + 1,
        "final_response": {
            "type":     "clarification",
            "question": state.get("clarifying_question",
                        "Could you tell me more about what you're experiencing?"),
            "possible_causes": state.get("possible_causes", []),
            "clinical_signals": state.get("possible_causes", []),
        },
        "nodes_visited": state.get("nodes_visited", []) + ["clarify"],
    }


def route_after_clarify(state: MedState) -> str:
    """After clarify — always go back to intent with enriched context."""
    return "intent"


# ── Build the graph ────────────────────────────────────────────────────────────
def build_graph():
    g = StateGraph(MedState)

    # Register nodes
    g.add_node("intent",   run_intent_node)
    g.add_node("clarify",  clarify_node)
    g.add_node("provider", run_provider_node)
    g.add_node("cost",     run_cost_node)
    g.add_node("response", run_response_node)

    # Entry point
    g.set_entry_point("intent")

    # intent → conditional branch
    g.add_conditional_edges("intent", route_after_intent, {
        "clarify":  "clarify",
        "provider": "provider",
    })

    # clarify → END (frontend re-sends with user's answer appended to history)
    g.add_edge("clarify", END)

    # Linear: provider → cost → response → END
    g.add_edge("provider", "cost")
    g.add_edge("cost",     "response")
    g.add_edge("response", END)

    return g.compile()


# ── Compiled graph (import this in main.py) ────────────────────────────────────
graph = build_graph()
print("✅ LangGraph compiled successfully")


# ── Helper: run full pipeline ──────────────────────────────────────────────────
async def run_graph(
    user_input:           str,
    user_profile:         dict,
    user_financials:      dict = None,
    session_id:           str  = None,
    conversation_history: list = None,
    selected_hospital:    str  = None,
    user_lat:             float = None,
    user_lon:             float = None,
) -> dict:
    """
    Main entry point called by FastAPI.
    Returns final_response dict.
    """
    # Compatibility for older LangGraph with newer LangChain packages.
    try:
        import langchain
        if not hasattr(langchain, "debug"):
            langchain.debug = False
    except Exception:
        pass

    previous_clarifications = 0
    for turn in conversation_history or []:
        assistant_text = (turn.get("assistant") or "").lower()
        if (
            turn.get("type") == "clarification"
            or "could you tell me more" in assistant_text
            or "describe the pain" in assistant_text
            or "describe your pain" in assistant_text
        ):
            previous_clarifications += 1

    initial_state: MedState = {
        "user_input":           user_input,
        "session_id":           session_id or "default",
        "user_profile":         user_profile or {},
        "user_financials":      user_financials or {},
        "conversation_history": conversation_history or [],
        "selected_hospital":    selected_hospital,
        "nodes_visited":        [],
        "clarify_attempts":     previous_clarifications,
        "is_emergency":         False,
        "recommendation_ready": False,
        "emergency_confidence": 0.0,
        "ambiguity_score":      0.5,
        "hospitals":            [],
        "possible_causes":      [],
        "user_lat":             user_lat,
        "user_lon":             user_lon,
    }

    result = await graph.ainvoke(initial_state)
    return result.get("final_response", {})
