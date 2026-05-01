import os
import uuid
from supabase import create_client, Client
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

# ── Supabase client ────────────────────────────────────────────────────────────
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
print("✅ Supabase connected")


# ── UUID helper ───────────────────────────────────────────────────────────────

def to_uuid(user_id: str) -> str:
    """
    Convert any plain string user ID (e.g. "test_user_1") to a deterministic
    UUID v5. The same input always produces the same UUID, preserving session
    continuity across restarts. Satisfies Supabase's uuid column type without
    any schema changes.
    """
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, user_id))


# ══════════════════════════════════════════════════════════════════════════════
# USER PROFILES
# ══════════════════════════════════════════════════════════════════════════════

def save_user_profile(user_id: str, profile: dict) -> bool:
    """Save or update user health profile."""
    try:
        data = {
            "user_id":                 to_uuid(user_id),
            "full_name":               profile.get("name"),
            "age":                     profile.get("age"),
            "gender":                  profile.get("gender"),
            "city":                    profile.get("city"),
            "blood_group":             profile.get("blood_group"),
            "comorbidities":           profile.get("comorbidities", []),
            "insurance_provider":      profile.get("insurance_provider"),
            "insurance_coverage_inr":  profile.get("insurance_coverage", 0),
            "has_insurance":           bool(profile.get("insurance_provider")),
            "income_band":             profile.get("income_band"),
            "employment_type":         profile.get("employment_type"),
            "emergency_contact_name":  profile.get("emergency_contact_name"),
            "emergency_contact_phone": profile.get("emergency_contact_phone"),
            "updated_at":              datetime.utcnow().isoformat(),
        }
        supabase.table("user_profiles").upsert(data, on_conflict="user_id").execute()
        return True
    except Exception as e:
        print(f"❌ save_user_profile error: {e}")
        return False


def get_user_profile(user_id: str) -> dict | None:
    """Load user health profile. Maps Supabase column names back to internal names."""
    try:
        res = (
            supabase.table("user_profiles")
            .select("*")
            .eq("user_id", to_uuid(user_id))
            .single()
            .execute()
        )
        if res.data:
            data = res.data
            data["name"]               = data.pop("full_name", None)
            data["insurance_coverage"] = data.pop("insurance_coverage_inr", 0)
            return data
        return None
    except Exception as e:
        print(f"❌ get_user_profile error: {e}")
        return None


# ══════════════════════════════════════════════════════════════════════════════
# USER FINANCIALS
# ══════════════════════════════════════════════════════════════════════════════

def save_user_financials(user_id: str, financials: dict) -> bool:
    """Save or update extracted financial data."""
    try:
        data = {
            "user_id":               to_uuid(user_id),
            "monthly_income_inr":    financials.get("monthly_income"),
            "annual_income_inr":     financials.get("annual_income"),
            "income_source":         financials.get("employment_type"),
            "cibil_score":           financials.get("cibil_score"),
            "total_emi_inr":         financials.get("existing_emi", 0),
            "foir":                  financials.get("foir_headroom"),
            "max_loan_eligible_inr": financials.get("max_loan_eligible"),
            # employment_years has no dedicated Supabase column.
            # We store it in risk_band as a string so it survives DB round-trips.
            "employment_years":      financials.get("employment_years"),
            "updated_at":            datetime.utcnow().isoformat(),
        }
        supabase.table("user_financials").upsert(data, on_conflict="user_id").execute()
        return True
    except Exception as e:
        print(f"❌ save_user_financials error: {e}")
        return False


def get_user_financials(user_id: str) -> dict | None:
    """Load user financial data. Maps Supabase column names back to internal names."""
    try:
        res = (
            supabase.table("user_financials")
            .select("*")
            .eq("user_id", to_uuid(user_id))
            .single()
            .execute()
        )
        if res.data:
            data = res.data
            data["monthly_income"]    = data.pop("monthly_income_inr", None)
            data["annual_income"]     = data.pop("annual_income_inr", None)
            data["employment_type"]   = data.pop("income_source", None)
            data["existing_emi"]      = data.pop("total_emi_inr", 0) or 0
            data["foir_headroom"]     = data.pop("foir", None)
            data["max_loan_eligible"] = data.pop("max_loan_eligible_inr", None)
            # Recover employment_years from risk_band (where we stored it)
            data["employment_years"] = float(data.pop("employment_years", None) or 2.0)
            return data
        return None
    except Exception as e:
        print(f"❌ get_user_financials error: {e}")
        return None


# ══════════════════════════════════════════════════════════════════════════════
# USER DOCUMENTS
# ══════════════════════════════════════════════════════════════════════════════

def save_document_metadata(user_id: str, doc_type: str,
                            filename: str, extracted: bool = False) -> bool:
    """Track uploaded document metadata."""
    try:
        data = {
            "user_id":           to_uuid(user_id),
            "doc_type":          doc_type,
            "file_name":         filename,
            "extraction_status": "done" if extracted else "pending",
            "uploaded_at":       datetime.utcnow().isoformat(),
        }
        supabase.table("user_documents").insert(data).execute()
        return True
    except Exception as e:
        print(f"❌ save_document_metadata error: {e}")
        return False


def get_user_documents(user_id: str) -> list[dict]:
    """Get all documents for a user."""
    try:
        res = (
            supabase.table("user_documents")
            .select("*")
            .eq("user_id", to_uuid(user_id))
            .execute()
        )
        return res.data or []
    except Exception as e:
        print(f"❌ get_user_documents error: {e}")
        return []


def mark_document_extracted(user_id: str, doc_type: str) -> bool:
    """Mark a document as extracted by Gemini."""
    try:
        (
            supabase.table("user_documents")
            .update({"extraction_status": "done"})
            .eq("user_id", to_uuid(user_id))
            .eq("doc_type", doc_type)
            .execute()
        )
        return True
    except Exception as e:
        print(f"❌ mark_document_extracted error: {e}")
        return False


# ══════════════════════════════════════════════════════════════════════════════
# SESSIONS (conversation state)
# ══════════════════════════════════════════════════════════════════════════════

def save_session(session_id: str, state: dict, user_id: str = None) -> bool:
    """
    Save full LangGraph state for a session.
    session_id is already a uuid4 string from main.py — no conversion needed.
    Pass user_id so the sessions.user_id FK is satisfied.
    """
    try:
        data = {
            "id":                 session_id,
            "langgraph_state":    state,
            "resolved_city":      state.get("last_city"),
            "resolved_procedure": state.get("last_procedure"),
            "last_active_at":     datetime.utcnow().isoformat(),
            
        }
        if user_id:
            data["user_id"] = user_id

        supabase.table("sessions").upsert(data, on_conflict="id").execute()
        return True
    except Exception as e:
        print(f"❌ save_session error: {e}")
        return False


def get_session(session_id: str) -> dict | None:
    """Load session state."""
    try:
        res = (
            supabase.table("sessions")
            .select("langgraph_state")
            .eq("id", session_id)
            .single()
            .execute()
        )
        if res.data and res.data.get("langgraph_state"):
            return res.data["langgraph_state"]
        return None
    except Exception as e:
        print(f"❌ get_session error: {e}")
        return None


def delete_session(session_id: str) -> bool:
    """Delete a session (new conversation)."""
    try:
        supabase.table("sessions").delete().eq("id", session_id).execute()
        return True
    except Exception as e:
        print(f"❌ delete_session error: {e}")
        return False


# ══════════════════════════════════════════════════════════════════════════════
# QUERY LOGS
# ══════════════════════════════════════════════════════════════════════════════

def log_query(session_id: str, user_id: str, state: dict) -> bool:
    """Log every query for demo + debugging."""
    try:
        data = {
            "session_id":      session_id,
            "user_id":         to_uuid(user_id),
            "user_message":    state.get("user_input", ""),
            "intent_detected": state.get("procedure"),
            "city_detected":   state.get("city"),
            "mode_detected":   "emergency" if state.get("is_emergency") else "standard",
            "node_trace":      state.get("nodes_visited", []),
            "logged_at":       datetime.utcnow().isoformat(),
        }
        supabase.table("query_logs").insert(data).execute()
        return True
    except Exception as e:
        print(f"❌ log_query error: {e}")
        return False


def get_recent_queries(user_id: str, limit: int = 10) -> list[dict]:
    """Get recent queries for a user."""
    try:
        res = (
            supabase.table("query_logs")
            .select("*")
            .eq("user_id", to_uuid(user_id))
            .order("logged_at", desc=True)
            .limit(limit)
            .execute()
        )
        return res.data or []
    except Exception as e:
        print(f"❌ get_recent_queries error: {e}")
        return []