import os
import uuid
import json
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

from graph import run_graph
from db import (
    save_user_profile, get_user_profile,
    get_user_profile_by_email, hash_password, verify_password, to_uuid,
    save_user_financials, get_user_financials,
    save_document_metadata, get_user_documents, save_document_with_url,
    update_document_extraction, delete_user_document,
    get_user_document, update_user_document_file,
    save_session, get_session,
    log_query,
    save_loan_application, get_loan_application,
    update_loan_status, get_all_loan_applications, get_user_loan_applications,
)

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
gemini = genai.GenerativeModel("gemini-2.5-flash")
DOCUMENT_EXTRACTION_ENABLED = os.getenv("DOCUMENT_EXTRACTION_ENABLED", "false").lower() == "true"
DOCUMENT_BUCKET = os.getenv("DOCUMENT_BUCKET", "medical-documents")

app = FastAPI(title="MedPath AI", version="1.0.0")

# ── CORS — allow React frontend ────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ══════════════════════════════════════════════════════════════════════════════
# REQUEST MODELS
# ══════════════════════════════════════════════════════════════════════════════

class ChatRequest(BaseModel):
    message:           str
    user_id:           str
    session_id:        Optional[str]   = None
    selected_hospital: Optional[str]   = None
    user_lat:          Optional[float] = None
    user_lon:          Optional[float] = None

class RegisterRequest(BaseModel):
    user_id:                 str
    email:                   str
    password:                Optional[str] = None
    name:                    str
    age:                     int
    gender:                  str
    city:                    str
    blood_group:             Optional[str] = None
    comorbidities:           list[str]     = []
    insurance_provider:      Optional[str] = None
    insurance_coverage:      Optional[int] = 0
    income_band:             Optional[str] = None
    emergency_contact_name:  Optional[str] = None
    emergency_contact_phone: Optional[str] = None

class FinancialsRequest(BaseModel):
    user_id:          str
    employment_type:  str
    monthly_income:   int   = Field(gt=0)
    existing_emi:     int   = Field(default=0, ge=0)
    cibil_score:      int   = Field(ge=300, le=900)
    employment_years: float = Field(ge=0)

class LoanApplyRequest(BaseModel):
    user_id:            str
    session_id:         str
    loan_amount:        int
    tenure_months:      int
    selected_hospital:  Optional[str] = None

class LoginRequest(BaseModel):
    email:    str
    password: str


DOC_VALIDATION_RULES = {
    "salary_slip": {
        "required_any": ["monthly_income", "employer", "employer_name"],
        "label": "salary slip",
    },
    "itr": {
        "required_any": ["annual_income", "monthly_income"],
        "label": "ITR document",
    },
    "balance_sheet": {
        "required_any": ["annual_income", "monthly_income", "net_worth", "total_assets"],
        "label": "balance sheet",
    },
    "cibil_report": {
        "required_any": ["cibil_score"],
        "label": "CIBIL report",
    },
    "insurance_policy": {
        "required_any": ["insurance_provider", "provider", "sum_insured", "insurance_coverage"],
        "label": "insurance document",
    },
    "medical_records": {
        "required_any": ["diagnosis", "procedure", "hospital", "doctor_name"],
        "label": "medical record",
    },
}

DOC_TYPE_ALIASES = {
    "cibil": "cibil_report",
    "insurance": "insurance_policy",
}

ALLOWED_DOC_TYPES = set(DOC_VALIDATION_RULES)


def normalize_doc_type(doc_type: str) -> str:
    """Map old UI aliases to the doc_type values allowed by Supabase."""
    normalized = (doc_type or "").strip().lower()
    return DOC_TYPE_ALIASES.get(normalized, normalized)


def validate_document_extraction(doc_type: str, extracted: dict) -> tuple[bool, str]:
    """Reject empty or wrong-type extraction before it affects financials."""
    rule = DOC_VALIDATION_RULES.get(doc_type)
    if not rule:
        return True, "Document uploaded"

    if not extracted:
        return False, f"This does not look like a valid {rule['label']}."

    has_required_signal = any(extracted.get(key) not in (None, "", []) for key in rule["required_any"])
    if not has_required_signal:
        return False, f"This does not look like a valid {rule['label']}."

    cibil_score = extracted.get("cibil_score")
    if cibil_score is not None:
        try:
            score = int(cibil_score)
            if score < 300 or score > 900:
                return False, "The extracted CIBIL score is outside the valid 300-900 range."
        except (TypeError, ValueError):
            return False, "The extracted CIBIL score is not a valid number."

    return True, "Document verified and extracted"

# ══════════════════════════════════════════════════════════════════════════════
# HEALTH CHECK
# ══════════════════════════════════════════════════════════════════════════════

@app.get("/")
def root():
    return {"status": "MedPath AI is running 🚀"}

@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/api/meta/cities")
def get_cities():
    """Return supported cities for registration."""
    fallback_cities = [
        "Mumbai", "Delhi", "Bengaluru", "Hyderabad", "Chennai",
        "Kolkata", "Pune", "Ahmedabad", "Jaipur", "Lucknow",
        "Nagpur", "Indore", "Coimbatore", "Surat", "Bhopal",
    ]
    try:
        from data_loader import cities_df
        cities = (
            cities_df["city"]
            .dropna()
            .astype(str)
            .sort_values()
            .unique()
            .tolist()
        )
        return {"cities": cities or fallback_cities}
    except Exception as e:
        print(f"Could not load cities from data source: {e}")
        return {"cities": fallback_cities}

# ══════════════════════════════════════════════════════════════════════════════
# REGISTRATION
# ══════════════════════════════════════════════════════════════════════════════

@app.post("/api/register")
async def register(req: RegisterRequest):
    """Save user health profile."""
    profile = req.model_dump()

    existing = get_user_profile_by_email(req.email)
    request_uuid = to_uuid(req.user_id)
    if existing and existing.get("user_id") != request_uuid:
        raise HTTPException(status_code=409, detail="An account with this email already exists")

    profile["email"] = req.email.strip().lower()
    if req.password:
        if len(req.password) < 8:
            raise HTTPException(status_code=400, detail="Password must be at least 8 characters")
        profile["password_hash"] = hash_password(req.password)
    elif not existing:
        raise HTTPException(status_code=400, detail="Password is required for new accounts")

    success = save_user_profile(req.user_id, profile)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to save profile")
    return {"success": True, "message": "Profile saved successfully", "user_id": request_uuid}


@app.post("/api/login")
async def login(req: LoginRequest):
    """Authenticate an existing MedPath profile."""
    profile = get_user_profile_by_email(req.email, include_sensitive=True)
    if not profile or not verify_password(req.password, profile.get("password_hash")):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    profile.pop("password_hash", None)
    user_id    = profile.get("user_id")
    financials = get_user_financials(user_id)
    documents  = get_user_documents(user_id)

    return {
        "success":    True,
        "user_id":    user_id,
        "profile":    profile,
        "financials": financials,
        "documents":  documents,
    }


@app.get("/api/profile/{user_id}")
async def get_profile(user_id: str):
    """Get user profile + financials + documents."""
    profile    = get_user_profile(user_id)
    financials = get_user_financials(user_id)
    documents  = get_user_documents(user_id)

    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    return {
        "profile":    profile,
        "financials": financials,
        "documents":  documents,
    }

# ══════════════════════════════════════════════════════════════════════════════
# FINANCIALS
# ══════════════════════════════════════════════════════════════════════════════

@app.post("/api/financials")
async def save_financials(req: FinancialsRequest):
    """Save user financial details manually entered."""
    financials = req.model_dump()

    max_loan      = req.monthly_income * 10
    foir_headroom = (req.monthly_income * 0.50 - req.existing_emi) / req.monthly_income \
                    if req.monthly_income > 0 else 0.0
    financials["max_loan_eligible"] = min(max_loan, 3_000_000)
    financials["foir_headroom"]     = round(foir_headroom, 2)
    financials["income_stable"]     = True

    success = save_user_financials(req.user_id, financials)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to save financials")

    return {
        "success":           True,
        "max_loan_eligible": financials["max_loan_eligible"],
        "foir_headroom":     financials["foir_headroom"],
    }

# ══════════════════════════════════════════════════════════════════════════════
# DOCUMENT UPLOAD
# ══════════════════════════════════════════════════════════════════════════════

@app.post("/api/documents/upload")
async def upload_document(
    user_id:  str        = Form(...),
    doc_type: str        = Form(...),
    file:     UploadFile = File(...),
):
    """
    Upload financial document (PDF, JPG, PNG, WEBP).
    Saves to Supabase Storage. Gemini extraction is optional via env flag.
    """
    contents = await file.read()
    original_filename = file.filename or "document"
    doc_type = normalize_doc_type(doc_type)

    if doc_type not in ALLOWED_DOC_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported document type '{doc_type}'.",
        )

    # ── Save file to Supabase Storage ─────────────────────────────────────────
    file_url = None
    storage_path = f"{to_uuid(user_id)}/{doc_type}/{uuid.uuid4()}-{original_filename}"
    try:
        from db import supabase
        supabase.storage.from_(DOCUMENT_BUCKET).upload(
            path=storage_path,
            file=contents,
            file_options={"content-type": file.content_type or "application/octet-stream"},
        )
        file_url = supabase.storage.from_(DOCUMENT_BUCKET).get_public_url(storage_path)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Could not upload document to Supabase Storage bucket '{DOCUMENT_BUCKET}'.",
        ) from e
        print(f"⚠️  Storage upload failed (continuing without URL): {e}")

    # ── Save metadata with URL ────────────────────────────────────────────────
    metadata_saved = False
    initial_status = "pending"
    if file_url:
        metadata_saved = save_document_with_url(
            user_id, doc_type, original_filename, file_url,
            extracted=False, storage_path=storage_path,
            file_size_bytes=len(contents), mime_type=file.content_type,
            extraction_status=initial_status,
        )
    else:
        metadata_saved = save_document_metadata(
            user_id, doc_type, original_filename,
            extracted=False, storage_path=storage_path,
            file_size_bytes=len(contents), mime_type=file.content_type,
            extraction_status=initial_status,
        )

    if not metadata_saved:
        raise HTTPException(
            status_code=500,
            detail="Document file was received, but its metadata could not be saved.",
        )

    if not DOCUMENT_EXTRACTION_ENABLED:
        return {
            "success":   True,
            "extracted": {},
            "file_url":  file_url,
            "message":   f"{doc_type} uploaded for manual PFL verification.",
        }

    # ── Gemini extraction ─────────────────────────────────────────────────────
    try:
        import base64
        b64 = base64.b64encode(contents).decode()

        extract_prompt = f"""
        This is a {doc_type} document from India.
        Extract the following financial information and return ONLY valid JSON:
        {{
          "monthly_income":   <integer or null>,
          "annual_income":    <integer or null>,
          "income_stable":    <true/false>,
          "cibil_score":      <integer or null>,
          "existing_emi":     <integer or null>,
          "employer":         <string or null>,
          "employment_years": <float or null>
        }}
        Return ONLY JSON. No explanation. No markdown.
        """

        filename = file.filename.lower()
        if filename.endswith(".pdf"):
            mime = "application/pdf"
        elif filename.endswith(".png"):
            mime = "image/png"
        elif filename.endswith((".jpg", ".jpeg")):
            mime = "image/jpeg"
        elif filename.endswith(".webp"):
            mime = "image/webp"
        else:
            return {
                "success":   False,
                "extracted": {},
                "message":   "Unsupported file type. Please upload PDF, JPG, PNG, or WEBP."
            }

        response = gemini.generate_content([
            {"mime_type": mime, "data": b64},
            extract_prompt,
        ])

        raw = response.text.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.strip()

        extracted = json.loads(raw)
        if not isinstance(extracted, dict):
            extracted = {}

        is_valid, validation_summary = validate_document_extraction(doc_type, extracted)
        if not is_valid:
            update_document_extraction(
                user_id=user_id,
                doc_type=doc_type,
                storage_path=storage_path,
                extracted_json=extracted,
                status="failed",
                summary=validation_summary,
                confidence=0.0,
            )
            return {
                "success":   False,
                "extracted": extracted,
                "file_url":  file_url,
                "message":   validation_summary,
            }

        # Merge extracted data into existing financials
        current = get_user_financials(user_id) or {}
        for key, val in extracted.items():
            if val is not None:
                current[key] = val
        current["user_id"] = user_id
        save_user_financials(user_id, current)
        update_document_extraction(
            user_id=user_id,
            doc_type=doc_type,
            storage_path=storage_path,
            extracted_json=extracted,
            status="done",
            summary=validation_summary,
            confidence=0.8 if extracted else 0.0,
        )

        return {
            "success":   True,
            "extracted": extracted,
            "file_url":  file_url,
            "message":   f"{doc_type} processed successfully",
        }

    except Exception as e:
        print(f"❌ Document extraction error: {e}")
        update_document_extraction(
            user_id=user_id,
            doc_type=doc_type,
            storage_path=storage_path,
            extracted_json={},
            status="failed",
            summary=str(e)[:500],
            confidence=0.0,
        )
        return {
            "success":   True,
            "extracted": {},
            "file_url":  file_url,
            "message":   "Document saved. Manual extraction may be needed.",
        }


@app.get("/api/documents/{user_id}")
async def get_documents(user_id: str):
    """Get all uploaded documents for a user."""
    docs = get_user_documents(user_id)
    return {"documents": docs}


@app.put("/api/documents/{user_id}/{document_id}/file")
async def replace_document_file(
    user_id: str,
    document_id: str,
    file: UploadFile = File(...),
):
    """Replace the stored file for an uploaded document."""
    existing = get_user_document(user_id, document_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Document not found")

    contents = await file.read()
    original_filename = file.filename or "document"
    doc_type = normalize_doc_type(existing.get("doc_type"))
    storage_path = f"{to_uuid(user_id)}/{doc_type}/{uuid.uuid4()}-{original_filename}"

    try:
        from db import supabase
        supabase.storage.from_(DOCUMENT_BUCKET).upload(
            path=storage_path,
            file=contents,
            file_options={"content-type": file.content_type or "application/octet-stream"},
        )
        file_url = supabase.storage.from_(DOCUMENT_BUCKET).get_public_url(storage_path)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Could not upload replacement document to Supabase Storage bucket '{DOCUMENT_BUCKET}'.",
        ) from e

    status = "pending"
    success = update_user_document_file(
        user_id=user_id,
        document_id=document_id,
        file_name=original_filename,
        storage_path=storage_path,
        file_url=file_url,
        file_size_bytes=len(contents),
        mime_type=file.content_type,
        extraction_status=status,
    )
    if not success:
        try:
            from db import supabase
            supabase.storage.from_(DOCUMENT_BUCKET).remove([storage_path])
        except Exception as e:
            print(f"Replacement cleanup failed: {e}")
        raise HTTPException(status_code=404, detail="Document not found")

    old_storage_path = existing.get("storage_path")
    if old_storage_path:
        try:
            from db import supabase
            supabase.storage.from_(DOCUMENT_BUCKET).remove([old_storage_path])
        except Exception as e:
            print(f"Old document cleanup failed: {e}")

    return {
        "success": True,
        "file_url": file_url,
        "message": f"{doc_type} replaced successfully.",
    }


@app.delete("/api/documents/{user_id}/{document_id}")
async def delete_document(user_id: str, document_id: str):
    """Delete one uploaded document so the user can replace it later."""
    success = delete_user_document(user_id, document_id)
    if not success:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"success": True}

# ══════════════════════════════════════════════════════════════════════════════
# MAIN CHAT ENDPOINT
# ══════════════════════════════════════════════════════════════════════════════

@app.post("/api/chat")
async def chat(req: ChatRequest):
    """
    Main chat endpoint.
    Runs the full LangGraph pipeline and returns structured response.
    """
    session_id = req.session_id or str(uuid.uuid4())

    profile = get_user_profile(req.user_id)
    if not profile:
        raise HTTPException(
            status_code=404,
            detail="User profile not found. Please complete registration first."
        )

    financials    = get_user_financials(req.user_id)
    session_state = get_session(session_id)
    history       = session_state.get("conversation_history", []) if session_state else []

    result = await run_graph(
        user_input           = req.message,
        user_profile         = profile,
        user_financials      = financials,
        session_id           = session_id,
        conversation_history = history,
        selected_hospital    = req.selected_hospital,
        user_lat             = req.user_lat,
        user_lon             = req.user_lon,
    )

    history.append({
        "user":      req.message,
        "assistant": result.get("explanation") or result.get("question", ""),
        "type":      result.get("type", "recommendation"),
    })

    save_session(session_id, {
        "conversation_history": history,
        "last_hospitals":       result.get("hospitals", []),
        "last_procedure":       result.get("procedure"),
        "last_city":            result.get("city"),
    }, user_id=req.user_id)

    log_query(session_id, req.user_id, {
        "user_input":    req.message,
        "procedure":     result.get("procedure"),
        "city":          result.get("city"),
        "is_emergency":  result.get("is_emergency"),
        "nodes_visited": result.get("graph_path", "").replace(" → ", " -> ").split(" -> "),
    })

    return {
        "session_id": session_id,
        "response":   result,
    }

# ══════════════════════════════════════════════════════════════════════════════
# LOAN APPLICATION
# ══════════════════════════════════════════════════════════════════════════════

@app.post("/api/loan/apply")
async def apply_loan(req: LoanApplyRequest):
    """
    User confirms loan application.
    1. Runs eligibility check using loan_engine
    2. If GREEN or YELLOW — packages application + documents, saves to Supabase
    3. Returns result so frontend can show offer or alternatives
    """
    from loan_engine import run_eligibility, build_application_package

    profile    = get_user_profile(req.user_id)
    financials = get_user_financials(req.user_id)
    documents  = get_user_documents(req.user_id)

    if not financials or not financials.get("monthly_income"):
        return {
            "success":  False,
            "decision": "UNKNOWN",
            "message":  "Please upload your financial documents first.",
        }

    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    # ── Step 1: Run eligibility ────────────────────────────────────────────────
    eligibility = run_eligibility(
        loan_amount      = req.loan_amount,
        monthly_income   = financials.get("monthly_income") or 0,
        existing_emi     = financials.get("existing_emi") or 0,
        cibil_score      = financials.get("cibil_score") or 700,
        employment_years = financials.get("employment_years") or 2.0,
        age              = profile.get("age") or 35,
    )

    # ── Step 2: If RED — return immediately, don't send to PFL ────────────────
    if eligibility["decision"] == "RED":
        return {
            "success":      True,
            "decision":     "RED",
            "checks":       eligibility["checks"],
            "flags":        eligibility["flags"],
            "alternatives": eligibility["alternatives"],
            "message":      "You don't qualify for this loan amount right now. See alternatives below.",
            "sent_to_pfl":  False,
        }

    # ── Step 3: Get hospital + procedure from session ─────────────────────────
    session_state = get_session(req.session_id) or {}
    hospitals     = session_state.get("last_hospitals", [])
    procedure     = session_state.get("last_procedure", "Medical procedure")
    selected      = None
    if req.selected_hospital:
        selected = next(
            (h for h in hospitals if str(h.get("hospital_id")) == str(req.selected_hospital)),
            None,
        )
    selected      = selected or (hospitals[0] if hospitals else {})
    hospital_name = selected.get("hospital_name") or selected.get("name") or "Selected Hospital"

    # ── Step 4: Build and save application package ────────────────────────────
    ref_id, application = build_application_package(
        user_id       = req.user_id,
        profile       = profile,
        financials    = financials,
        documents     = documents,
        loan_amount   = req.loan_amount,
        tenure_months = req.tenure_months,
        hospital_name = hospital_name,
        procedure     = procedure,
        eligibility   = eligibility,
    )

    if not save_loan_application(ref_id, req.user_id, application):
        raise HTTPException(
            status_code=500,
            detail="Could not save loan application. Please try again.",
        )

    log_query(req.session_id, req.user_id, {
        "user_input":    f"Loan application ₹{req.loan_amount:,} ref:{ref_id}",
        "nodes_visited": ["loan_apply"],
    })

    return {
        "success":      True,
        "decision":     eligibility["decision"],
        "reference_id": ref_id,
        "checks":       eligibility["checks"],
        "flags":        eligibility["flags"],
        "offer":        eligibility["offer"],
        "message":      (
            "Your application has been submitted to Poonawalla Fincorp."
            if eligibility["decision"] == "GREEN"
            else "Application submitted. PFL will verify your documents."
        ),
        "sent_to_pfl":  True,
        "status":       "PENDING",
    }


@app.get("/api/loan/status/{reference_id}")
async def loan_status(reference_id: str):
    """
    Patient polls this every 3 seconds after submitting.
    Returns current status: PENDING / APPROVED / REJECTED
    """
    application = get_loan_application(reference_id)
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    return {
        "reference_id":  application["reference_id"],
        "status":        application["status"],
        "officer_note":  application.get("officer_note"),
        "decided_at":    application.get("decided_at"),
        "loan_amount":   application.get("loan_amount"),
        "emi":           application.get("emi"),
        "interest_rate": application.get("interest_rate"),
        "tenure_months": application.get("tenure_months"),
        "hospital_name": application.get("hospital_name"),
    }


@app.get("/api/loan/applications/{user_id}")
async def user_loan_applications(user_id: str):
    """Patient loan history - returns only applications owned by this user."""
    applications = get_user_loan_applications(user_id)
    return {"applications": applications}


@app.post("/api/pfl/decide")
async def pfl_decide(
    reference_id: str,
    decision:     str,
    officer_note: str = "",
):
    """
    PFL officer approves or rejects from the dashboard.
    decision must be APPROVED or REJECTED.
    """
    if decision not in ("APPROVED", "REJECTED"):
        raise HTTPException(status_code=400, detail="decision must be APPROVED or REJECTED")

    success = update_loan_status(reference_id, decision, officer_note)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to update status")

    return {"success": True, "reference_id": reference_id, "status": decision}


@app.get("/api/pfl/applications")
async def pfl_applications():
    """
    PFL officer dashboard — returns all applications newest first.
    The React PFL dashboard polls this endpoint every 3 seconds.
    """
    applications = get_all_loan_applications()
    return {"applications": applications}

# ══════════════════════════════════════════════════════════════════════════════
# RUN SERVER
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
