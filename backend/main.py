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
    save_document_metadata, get_user_documents,
    save_session, get_session,
    log_query
)

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
gemini = genai.GenerativeModel("gemini-2.5-flash")

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
    session_id:        Optional[str]  = None
    selected_hospital: Optional[str]  = None
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
    blood_group:             Optional[str]  = None
    comorbidities:           list[str]      = []
    insurance_provider:      Optional[str]  = None
    insurance_coverage:      Optional[int]  = 0
    income_band:             Optional[str]  = None
    emergency_contact_name:  Optional[str]  = None
    emergency_contact_phone: Optional[str]  = None

class FinancialsRequest(BaseModel):
    user_id:          str
    employment_type:  str
    monthly_income:   int   = Field(gt=0)
    existing_emi:     int   = Field(default=0, ge=0)
    cibil_score:      int   = Field(ge=300, le=900)
    employment_years: float = Field(ge=0)

class LoanApplyRequest(BaseModel):
    user_id:       str
    session_id:    str
    loan_amount:   int
    tenure_months: int

class LoginRequest(BaseModel):
    email:    str
    password: str

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
    user_id = profile.get("user_id")
    financials = get_user_financials(user_id)
    documents = get_user_documents(user_id)

    return {
        "success": True,
        "user_id": user_id,
        "profile": profile,
        "financials": financials,
        "documents": documents,
    }


@app.get("/api/profile/{user_id}")
async def get_profile(user_id: str):
    """Get user profile + financials."""
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

    # Pre-calculate derived fields
    max_loan      = req.monthly_income * 10
    foir_headroom = (req.monthly_income * 0.50 - req.existing_emi) / req.monthly_income \
                    if req.monthly_income > 0 else 0.0
    financials["max_loan_eligible"] = min(max_loan, 3_000_000)
    financials["foir_headroom"]     = round(foir_headroom, 2)
    financials["income_stable"]     = True
    # employment_years is in financials dict — save_user_financials persists it via risk_band

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
    doc_type: str        = Form(...),   # salary_slip / itr / balance_sheet / insurance
    file:     UploadFile = File(...),
):
    """
    Upload financial document (PDF, JPG, PNG, WEBP).
    Gemini reads it and extracts key financial data.
    """
    contents = await file.read()

    # Save metadata first (before extraction attempt)
    save_document_metadata(user_id, doc_type, file.filename, extracted=False)

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

        # Merge extracted data into existing financials
        current = get_user_financials(user_id) or {}
        for key, val in extracted.items():
            if val is not None:
                current[key] = val
        current["user_id"] = user_id
        save_user_financials(user_id, current)

        return {
            "success":   True,
            "extracted": extracted,
            "message":   f"{doc_type} processed successfully"
        }

    except Exception as e:
        print(f"❌ Document extraction error: {e}")
        return {
            "success":   True,
            "extracted": {},
            "message":   "Document saved. Manual extraction may be needed."
        }


@app.get("/api/documents/{user_id}")
async def get_documents(user_id: str):
    """Get all uploaded documents for a user."""
    docs = get_user_documents(user_id)
    return {"documents": docs}

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

    # Load user profile
    profile = get_user_profile(req.user_id)
    if not profile:
        raise HTTPException(
            status_code=404,
            detail="User profile not found. Please complete registration first."
        )

    # Load financials (may be None if not yet uploaded)
    financials = get_user_financials(req.user_id)

    # Load conversation history from session
    session_state = get_session(session_id)
    history = session_state.get("conversation_history", []) if session_state else []

    # Run the LangGraph pipeline
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

    # Update conversation history
    history.append({
        "user":      req.message,
        "assistant": result.get("explanation") or result.get("question", ""),
        "type":      result.get("type", "recommendation"),
    })

    # Save session — pass user_id so FK is satisfied
    save_session(session_id, {
        "conversation_history": history,
        "last_hospitals":       result.get("hospitals", []),
        "last_procedure":       result.get("procedure"),
        "last_city":            result.get("city"),
    }, user_id=req.user_id)

    # Log query
    log_query(session_id, req.user_id, {
        "user_input":    req.message,
        "procedure":     result.get("procedure"),
        "city":          result.get("city"),
        "is_emergency":  result.get("is_emergency"),
        "nodes_visited": result.get("graph_path", "").split(" → "),
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
    User clicks Apply for PFL Loan.
    Runs eligibility check and marks as sent to PFL.
    """
    financials = get_user_financials(req.user_id)

    if not financials:
        return {
            "success":  False,
            "message":  "Please upload your financial documents first",
            "decision": "UNKNOWN"
        }

    from data_loader import check_loan_eligibility, calculate_pfl_options

    eligibility = check_loan_eligibility(
        loan_amount      = req.loan_amount,
        monthly_income   = financials.get("monthly_income") or 0,
        existing_emi     = financials.get("existing_emi") or 0,
        cibil_score      = financials.get("cibil_score") or 700,
        employment_years = financials.get("employment_years") or 2.0,
    )

    pfl_options = calculate_pfl_options(req.loan_amount)

    log_query(req.session_id, req.user_id, {
        "user_input":    f"Loan application for ₹{req.loan_amount:,}",
        "nodes_visited": ["loan_apply"],
    })

    return {
        "success":      True,
        "decision":     eligibility["decision"],
        "eligibility":  eligibility,
        "pfl_options":  pfl_options,
        "message":      eligibility["recommendation"],
        "sent_to_pfl":  eligibility["decision"] in ["GREEN", "YELLOW"],
        "pfl_contact":  (
            "A Poonawalla Fincorp representative will contact you within 24 hours."
            if eligibility["decision"] in ["GREEN", "YELLOW"] else None
        ),
    }

# ══════════════════════════════════════════════════════════════════════════════
# RUN SERVER
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
