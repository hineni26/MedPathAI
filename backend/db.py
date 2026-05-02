#hi
import os
import uuid
import base64
import hashlib
import hmac
import secrets
from supabase import create_client, Client
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

# ── Supabase client ────────────────────────────────────────────────────────────
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
DOCUMENT_BUCKET = os.getenv("DOCUMENT_BUCKET", "medical-documents")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
print("✅ Supabase connected")


# ── UUID helper ───────────────────────────────────────────────────────────────

DOC_TYPE_ALIASES = {
    "cibil": "cibil_report",
    "insurance": "insurance_policy",
}


def normalize_doc_type(doc_type: str) -> str:
    """Map old UI aliases to the doc_type values allowed by Supabase."""
    normalized = (doc_type or "").strip().lower()
    return DOC_TYPE_ALIASES.get(normalized, normalized)


def to_uuid(user_id: str) -> str:
    """
    Convert any plain string user ID (e.g. "test_user_1") to a deterministic
    UUID v5. The same input always produces the same UUID, preserving session
    continuity across restarts. Satisfies Supabase's uuid column type without
    any schema changes.
    """
    try:
        return str(uuid.UUID(user_id))
    except (TypeError, ValueError):
        return str(uuid.uuid5(uuid.NAMESPACE_DNS, user_id))


def hash_password(password: str) -> str:
    """Create a salted one-way password hash."""
    iterations = 210_000
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        iterations,
    )
    return "$".join([
        "pbkdf2_sha256",
        str(iterations),
        base64.b64encode(salt).decode("ascii"),
        base64.b64encode(digest).decode("ascii"),
    ])


def verify_password(password: str, password_hash: str | None) -> bool:
    """Verify a password against a stored PBKDF2 hash."""
    if not password_hash:
        return False

    try:
        scheme, iterations, salt_b64, digest_b64 = password_hash.split("$", 3)
        if scheme != "pbkdf2_sha256":
            return False
        salt = base64.b64decode(salt_b64)
        expected = base64.b64decode(digest_b64)
        actual = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            int(iterations),
        )
        return hmac.compare_digest(actual, expected)
    except Exception:
        return False


def _normalize_profile(data: dict, include_sensitive: bool = False) -> dict:
    data = dict(data)
    data["name"] = data.pop("full_name", None)
    data["insurance_coverage"] = data.pop("insurance_coverage_inr", 0)
    if not include_sensitive:
        data.pop("password_hash", None)
    return data


# ══════════════════════════════════════════════════════════════════════════════
# USER PROFILES
# ══════════════════════════════════════════════════════════════════════════════

def save_user_profile(user_id: str, profile: dict) -> bool:
    """Save or update user health profile."""
    try:
        data = {
            "user_id":                 to_uuid(user_id),
            "email":                   profile.get("email"),
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
        if profile.get("password_hash"):
            data["password_hash"] = profile.get("password_hash")
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
            return _normalize_profile(res.data)
        return None
    except Exception as e:
        print(f"❌ get_user_profile error: {e}")
        return None


def get_user_profile_by_email(email: str, include_sensitive: bool = False) -> dict | None:
    """Load a user profile by case-insensitive email."""
    try:
        res = (
            supabase.table("user_profiles")
            .select("*")
            .ilike("email", email.strip().lower())
            .single()
            .execute()
        )
        if res.data:
            return _normalize_profile(res.data, include_sensitive=include_sensitive)
        return None
    except Exception as e:
        print(f"get_user_profile_by_email error: {e}")
        return None


# ══════════════════════════════════════════════════════════════════════════════
# USER FINANCIALS
# ══════════════════════════════════════════════════════════════════════════════

def _normalize_cibil_score(value) -> int | None:
    if value in (None, ""):
        return None

    try:
        score = int(value)
    except (TypeError, ValueError):
        return None

    return score if 300 <= score <= 900 else None


def save_user_financials(user_id: str, financials: dict) -> bool:
    """Save or update extracted financial data."""
    try:
        data = {
            "user_id":               to_uuid(user_id),
            "monthly_income_inr":    financials.get("monthly_income"),
            "annual_income_inr":     financials.get("annual_income"),
            "income_source":         financials.get("employment_type"),
            "cibil_score":           _normalize_cibil_score(financials.get("cibil_score")),
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
                            filename: str, extracted: bool = False,
                            storage_path: str | None = None,
                            file_size_bytes: int | None = None,
                            mime_type: str | None = None,
                            extraction_status: str | None = None) -> bool:
    """Track uploaded document metadata."""
    try:
        doc_type = normalize_doc_type(doc_type)
        data = {
            "user_id":           to_uuid(user_id),
            "doc_type":          doc_type,
            "file_name":         filename,
            "file_size_bytes":   file_size_bytes,
            "mime_type":         mime_type,
            "storage_path":      storage_path or f"{to_uuid(user_id)}/{doc_type}/{filename}",
            "extraction_status": extraction_status or ("done" if extracted else "pending"),
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
        doc_type = normalize_doc_type(doc_type)
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


def update_document_extraction(
    user_id: str,
    doc_type: str,
    storage_path: str,
    extracted_json: dict,
    status: str = "done",
    summary: str | None = None,
    confidence: float | None = None,
) -> bool:
    """Save extracted fields back onto the uploaded document row."""
    try:
        doc_type = normalize_doc_type(doc_type)
        (
            supabase.table("user_documents")
            .update({
                "extraction_status": status,
                "extracted_json": extracted_json,
                "extraction_summary": summary,
                "gemini_confidence": confidence,
            })
            .eq("user_id", to_uuid(user_id))
            .eq("doc_type", doc_type)
            .eq("storage_path", storage_path)
            .execute()
        )
        return True
    except Exception as e:
        print(f"❌ update_document_extraction error: {e}")
        return False


def delete_user_document(user_id: str, document_id: str) -> bool:
    """Delete a user's document metadata and best-effort remove the storage object."""
    try:
        res = (
            supabase.table("user_documents")
            .select("id, storage_path")
            .eq("id", document_id)
            .eq("user_id", to_uuid(user_id))
            .single()
            .execute()
        )
        if not res.data:
            return False

        storage_path = res.data.get("storage_path")
        if storage_path:
            try:
                supabase.storage.from_(DOCUMENT_BUCKET).remove([storage_path])
            except Exception as e:
                print(f"⚠️  Storage delete failed (metadata will still be removed): {e}")

        (
            supabase.table("user_documents")
            .delete()
            .eq("id", document_id)
            .eq("user_id", to_uuid(user_id))
            .execute()
        )
        return True
    except Exception as e:
        print(f"❌ delete_user_document error: {e}")
        return False


# ══════════════════════════════════════════════════════════════════════════════
# SESSIONS (conversation state)
# ══════════════════════════════════════════════════════════════════════════════

def get_user_document(user_id: str, document_id: str) -> dict | None:
    """Get one document belonging to a user."""
    try:
        res = (
            supabase.table("user_documents")
            .select("*")
            .eq("id", document_id)
            .eq("user_id", to_uuid(user_id))
            .single()
            .execute()
        )
        return res.data or None
    except Exception as e:
        print(f"get_user_document error: {e}")
        return None


def update_user_document_file(
    user_id: str,
    document_id: str,
    file_name: str,
    storage_path: str,
    file_url: str | None,
    file_size_bytes: int,
    mime_type: str | None,
    extraction_status: str,
) -> bool:
    """Replace the stored file attached to an existing document row."""
    try:
        data = {
            "file_name": file_name,
            "storage_path": storage_path,
            "file_url": file_url,
            "file_size_bytes": file_size_bytes,
            "mime_type": mime_type,
            "extraction_status": extraction_status,
            "extracted_json": None,
            "extraction_summary": None,
            "gemini_confidence": None,
            "uploaded_at": datetime.utcnow().isoformat(),
        }
        res = (
            supabase.table("user_documents")
            .update(data)
            .eq("id", document_id)
            .eq("user_id", to_uuid(user_id))
            .execute()
        )
        return bool(res.data)
    except Exception as e:
        print(f"update_user_document_file error: {e}")
        return False


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
            data["user_id"] = to_uuid(user_id)

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
            .limit(1)
            .execute()
        )
        if res.data:
            return res.data[0].get("langgraph_state")
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

# LOAN APPLICATIONS
# ══════════════════════════════════════════════════════════════════════════════

def _as_int(value, default: int | None = None) -> int | None:
    if value in (None, ""):
        return default
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _as_float(value, default: float | None = None) -> float | None:
    if value in (None, ""):
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default

def save_loan_application(reference_id: str, user_id: str, application: dict) -> bool:
    """Save full loan application package to Supabase."""
    import json
    try:
        data = {
            "reference_id":       reference_id,
            "user_id":            to_uuid(user_id),
            "applicant_name":     application.get("applicant_name"),
            "age":                _as_int(application.get("age")),
            "city":               application.get("city"),
            "loan_amount":        _as_int(application.get("loan_amount")),
            "tenure_months":      _as_int(application.get("tenure_months")),
            "interest_rate":      _as_float(application.get("interest_rate", 9.99)),
            "emi":                _as_int(application.get("emi")),
            "processing_fee":     _as_int(application.get("processing_fee")),
            "hospital_name":      application.get("hospital_name"),
            "procedure":          application.get("procedure"),
            "monthly_income":     _as_int(application.get("monthly_income")),
            "existing_emi":       _as_int(application.get("existing_emi"), 0),
            "cibil_score":        _as_int(application.get("cibil_score")),
            "foir":               _as_float(application.get("foir")),
            "employment_years":   _as_float(application.get("employment_years")),
            "employment_type":    application.get("employment_type"),
            "medpath_decision":   application.get("medpath_decision"),
            "risk_band":          application.get("risk_band"),
            "eligibility_flags":  json.dumps(application.get("eligibility_flags", [])),
            "application_json":   json.dumps(application),
            "documents_json":     json.dumps(application.get("documents", [])),
            "status":             "PENDING",
            "applied_at":         datetime.utcnow().isoformat(),
        }
        supabase.table("loan_applications").insert(data).execute()
        return True
    except Exception as e:
        print(f"❌ save_loan_application error: {e}")
        return False


def get_loan_application(reference_id: str) -> dict | None:
    """Fetch a single loan application by reference ID."""
    try:
        res = (
            supabase.table("loan_applications")
            .select("*")
            .eq("reference_id", reference_id)
            .single()
            .execute()
        )
        return res.data or None
    except Exception as e:
        print(f"❌ get_loan_application error: {e}")
        return None


def update_loan_status(reference_id: str, status: str, officer_note: str = "") -> bool:
    """PFL officer approves or rejects an application."""
    try:
        supabase.table("loan_applications").update({
            "status":       status,
            "officer_note": officer_note,
            "decided_at":   datetime.utcnow().isoformat(),
            "updated_at":   datetime.utcnow().isoformat(),
        }).eq("reference_id", reference_id).execute()
        return True
    except Exception as e:
        print(f"❌ update_loan_status error: {e}")
        return False


def get_all_loan_applications() -> list[dict]:
    """PFL dashboard — get all applications, newest first."""
    try:
        res = (
            supabase.table("loan_applications")
            .select("*")
            .order("applied_at", desc=True)
            .execute()
        )
        return res.data or []
    except Exception as e:
        print(f"❌ get_all_loan_applications error: {e}")
        return []


def get_user_loan_applications(user_id: str) -> list[dict]:
    """Patient dashboard - get this user's loan applications, newest first."""
    try:
        res = (
            supabase.table("loan_applications")
            .select("*")
            .eq("user_id", to_uuid(user_id))
            .order("applied_at", desc=True)
            .execute()
        )
        return res.data or []
    except Exception as e:
        print(f"get_user_loan_applications error: {e}")
        return []


def save_document_with_url(user_id: str, doc_type: str,
                            filename: str, file_url: str,
                            extracted: bool = False,
                            storage_path: str | None = None,
                            file_size_bytes: int | None = None,
                            mime_type: str | None = None,
                            extraction_status: str | None = None) -> bool:
    """Save document metadata including the Supabase Storage URL."""
    try:
        doc_type = normalize_doc_type(doc_type)
        data = {
            "user_id":           to_uuid(user_id),
            "doc_type":          doc_type,
            "file_name":         filename,
            "file_size_bytes":   file_size_bytes,
            "mime_type":         mime_type,
            "storage_path":      storage_path or f"{to_uuid(user_id)}/{doc_type}/{filename}",
            "file_url":          file_url,
            "extraction_status": extraction_status or ("done" if extracted else "pending"),
            "uploaded_at":       datetime.utcnow().isoformat(),
        }
        supabase.table("user_documents").insert(data).execute()
        return True
    except Exception as e:
        print(f"❌ save_document_with_url error: {e}")
        return False
