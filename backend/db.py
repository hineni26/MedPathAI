import os
from supabase import create_client, Client
from dotenv import load_dotenv
from datetime import datetime
import json

load_dotenv()

# ── Supabase client ────────────────────────────────────────────────────────────
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
print("✅ Supabase connected")

# ══════════════════════════════════════════════════════════════════════════════
# USER PROFILES
# ══════════════════════════════════════════════════════════════════════════════

def save_user_profile(user_id: str, profile: dict) -> bool:
    """Save or update user health profile."""
    try:
        data = {
            "user_id":           user_id,
            "name":              profile.get("name"),
            "age":               profile.get("age"),
            "gender":            profile.get("gender"),
            "city":              profile.get("city"),
            "blood_group":       profile.get("blood_group"),
            "comorbidities":     profile.get("comorbidities", []),
            "insurance_provider":profile.get("insurance_provider"),
            "insurance_coverage":profile.get("insurance_coverage", 0),
            "income_band":       profile.get("income_band"),
            "emergency_contact_name":  profile.get("emergency_contact_name"),
            "emergency_contact_phone": profile.get("emergency_contact_phone"),
            "updated_at":        datetime.utcnow().isoformat(),
        }
        supabase.table("user_profiles").upsert(data).execute()
        return True
    except Exception as e:
        print(f"❌ save_user_profile error: {e}")
        return False


def get_user_profile(user_id: str) -> dict | None:
    """Load user health profile."""
    try:
        res = supabase.table("user_profiles")\
            .select("*")\
            .eq("user_id", user_id)\
            .single()\
            .execute()
        return res.data
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
            "user_id":           user_id,
            "employment_type":   financials.get("employment_type"),
            "monthly_income":    financials.get("monthly_income"),
            "income_stable":     financials.get("income_stable", True),
            "cibil_score":       financials.get("cibil_score"),
            "existing_emi":      financials.get("existing_emi", 0),
            "max_loan_eligible": financials.get("max_loan_eligible"),
            "foir_headroom":     financials.get("foir_headroom"),
            "updated_at":        datetime.utcnow().isoformat(),
        }
        supabase.table("user_financials").upsert(data).execute()
        return True
    except Exception as e:
        print(f"❌ save_user_financials error: {e}")
        return False


def get_user_financials(user_id: str) -> dict | None:
    """Load user financial data."""
    try:
        res = supabase.table("user_financials")\
            .select("*")\
            .eq("user_id", user_id)\
            .single()\
            .execute()
        return res.data
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
            "user_id":     user_id,
            "doc_type":    doc_type,
            "filename":    filename,
            "extracted":   extracted,
            "verified":    False,
            "uploaded_at": datetime.utcnow().isoformat(),
        }
        supabase.table("user_documents").insert(data).execute()
        return True
    except Exception as e:
        print(f"❌ save_document_metadata error: {e}")
        return False


def get_user_documents(user_id: str) -> list[dict]:
    """Get all documents for a user."""
    try:
        res = supabase.table("user_documents")\
            .select("*")\
            .eq("user_id", user_id)\
            .execute()
        return res.data or []
    except Exception as e:
        print(f"❌ get_user_documents error: {e}")
        return []


def mark_document_extracted(user_id: str, doc_type: str) -> bool:
    """Mark a document as extracted by Gemini."""
    try:
        supabase.table("user_documents")\
            .update({"extracted": True})\
            .eq("user_id", user_id)\
            .eq("doc_type", doc_type)\
            .execute()
        return True
    except Exception as e:
        print(f"❌ mark_document_extracted error: {e}")
        return False


# ══════════════════════════════════════════════════════════════════════════════
# SESSIONS (conversation state)
# ══════════════════════════════════════════════════════════════════════════════

def save_session(session_id: str, state: dict) -> bool:
    """Save full LangGraph state for a session."""
    try:
        data = {
            "session_id":  session_id,
            "state_json":  json.dumps(state),
            "updated_at":  datetime.utcnow().isoformat(),
        }
        supabase.table("sessions").upsert(data).execute()
        return True
    except Exception as e:
        print(f"❌ save_session error: {e}")
        return False


def get_session(session_id: str) -> dict | None:
    """Load session state."""
    try:
        res = supabase.table("sessions")\
            .select("state_json")\
            .eq("session_id", session_id)\
            .single()\
            .execute()
        if res.data:
            return json.loads(res.data["state_json"])
        return None
    except Exception as e:
        print(f"❌ get_session error: {e}")
        return None


def delete_session(session_id: str) -> bool:
    """Delete a session (new conversation)."""
    try:
        supabase.table("sessions")\
            .delete()\
            .eq("session_id", session_id)\
            .execute()
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
        cost = state.get("cost_result", {})
        data = {
            "session_id":       session_id,
            "user_id":          user_id,
            "user_input":       state.get("user_input", ""),
            "mapped_procedure": state.get("procedure"),
            "icd10_code":       state.get("icd10_code"),
            "location":         state.get("city"),
            "budget":           state.get("budget"),
            "is_emergency":     state.get("is_emergency", False),
            "cost_min":         cost.get("total_min"),
            "cost_max":         cost.get("total_max"),
            "confidence":       cost.get("confidence"),
            "hospital_count":   len(state.get("hospitals", [])),
            "graph_path":       " → ".join(state.get("nodes_visited", [])),
            "created_at":       datetime.utcnow().isoformat(),
        }
        supabase.table("query_logs").insert(data).execute()
        return True
    except Exception as e:
        print(f"❌ log_query error: {e}")
        return False


def get_recent_queries(user_id: str, limit: int = 10) -> list[dict]:
    """Get recent queries for a user."""
    try:
        res = supabase.table("query_logs")\
            .select("*")\
            .eq("user_id", user_id)\
            .order("created_at", desc=True)\
            .limit(limit)\
            .execute()
        return res.data or []
    except Exception as e:
        print(f"❌ get_recent_queries error: {e}")
        return []