import os
import uuid
import json
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

from graph import run_graph
from db import (
    save_user_profile, get_user_profile,
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
    message:            str
    user_id:            str
    session_id:         Optional[str] = None
    selected_hospital:  Optional[str] = None
    user_lat:           Optional[float] = None  # ADD THIS
    user_lon:           Optional[float] = None  # ADD THIS  # hospital_id after user selects

class RegisterRequest(BaseModel):
    user_id:                  str
    name:                     str
    age:                      int
    gender:                   str
    city:                     str
    blood_group:              Optional[str] = None
    comorbidities:            list[str] = []
    insurance_provider:       Optional[str] = None
    insurance_coverage:       Optional[int] = 0
    income_band:              Optional[str] = None
    emergency_contact_name:   Optional[str] = None
    emergency_contact_phone:  Optional[str] = None

class FinancialsRequest(BaseModel):
    user_id:          str
    employment_type:  str
    monthly_income:   int
    existing_emi:     int = 0
    cibil_score:      int
    employment_years: float

class LoanApplyRequest(BaseModel):
    user_id:    str
    session_id: str
    loan_amount: int
    tenure_months: int

# ══════════════════════════════════════════════════════════════════════════════
# HEALTH CHECK
# ══════════════════════════════════════════════════════════════════════════════

@app.get("/")
def root():
    return {"status": "MedPath AI is running 🚀"}

@app.get("/health")
def health():
    return {"status": "ok"}

# ══════════════════════════════════════════════════════════════════════════════
# REGISTRATION
# ══════════════════════════════════════════════════════════════════════════════

@app.post("/api/register")
async def register(req: RegisterRequest):
    """Save user health profile."""
    profile = req.dict()
    success = save_user_profile(req.user_id, profile)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to save profile")
    return {"success": True, "message": "Profile saved successfully"}


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
    from data_loader import check_loan_eligibility, calculate_pfl_options

    financials = req.dict()

    # Pre-calculate max loan eligible
    max_loan = req.monthly_income * 10
    foir_headroom = (req.monthly_income * 0.50 - req.existing_emi) / req.monthly_income
    financials["max_loan_eligible"] = min(max_loan, 3000000)
    financials["foir_headroom"]     = round(foir_headroom, 2)
    financials["income_stable"]     = True

    success = save_user_financials(req.user_id, financials)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to save financials")

    return {
        "success":          True,
        "max_loan_eligible": financials["max_loan_eligible"],
        "foir_headroom":     financials["foir_headroom"],
    }

# ══════════════════════════════════════════════════════════════════════════════
# DOCUMENT UPLOAD
# ══════════════════════════════════════════════════════════════════════════════

@app.post("/api/documents/upload")
async def upload_document(
    user_id:  str      = Form(...),
    doc_type: str      = Form(...),   # salary_slip / itr / balance_sheet / insurance
    file:     UploadFile = File(...),
):
    """
    Upload financial document.
    Gemini reads it and extracts key financial data.
    """
    contents = await file.read()

    # Save metadata
    save_document_metadata(user_id, doc_type, file.filename, extracted=False)

    # Try to extract data with Gemini
    try:
        import base64
        b64 = base64.b64encode(contents).decode()

        extract_prompt = f"""
        This is a {doc_type} document from India.
        Extract the following financial information and return ONLY valid JSON:
        {{
          "monthly_income": <integer or null>,
          "annual_income":  <integer or null>,
          "income_stable":  <true/false>,
          "cibil_score":    <integer or null>,
          "existing_emi":   <integer or null>,
          "employer":       <string or null>,
          "employment_years": <float or null>
        }}
        Return ONLY JSON. No explanation.
        """

        # For PDF documents
        if file.filename.endswith(".pdf"):
            response = gemini.generate_content([
                {"mime_type": "application/pdf", "data": b64},
                extract_prompt
            ])
        else:
            response = gemini.generate_content(extract_prompt)

        raw = response.text.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.strip()

        extracted = json.loads(raw)

        # Update financials in DB
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
            "success": True,
            "extracted": {},
            "message": "Document saved. Manual extraction may be needed."
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
    # Generate session_id if not provided
    session_id = req.session_id or str(uuid.uuid4())

    # Load user profile
    profile = get_user_profile(req.user_id)
    if not profile:
        raise HTTPException(
            status_code=404,
            detail="User profile not found. Please complete registration first."
        )

    # Load financials
    financials = get_user_financials(req.user_id)

    # Load conversation history from session
    session_state = get_session(session_id)
    history = session_state.get("conversation_history", []) if session_state else []

    # Run the graph
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
        "assistant": result.get("explanation", ""),
    })

    # Save session
    save_session(session_id, {
        "conversation_history": history,
        "last_hospitals":       result.get("hospitals", []),
        "last_procedure":       result.get("procedure"),
        "last_city":            result.get("city"),
    })

    # Log query
    log_query(session_id, req.user_id, {
        "user_input":    req.message,
        "procedure":     result.get("procedure"),
        "icd10_code":    result.get("icd10_code"),
        "city":          result.get("city"),
        "is_emergency":  result.get("is_emergency"),
        "hospitals":     result.get("hospitals", []),
        "cost_result":   result.get("cost_result"),
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
    profile    = get_user_profile(req.user_id)

    if not financials:
        return {
            "success":  False,
            "message":  "Please upload your financial documents first",
            "decision": "UNKNOWN"
        }

    from data_loader import check_loan_eligibility, calculate_pfl_options

    eligibility = check_loan_eligibility(
        loan_amount      = req.loan_amount,
        monthly_income   = financials.get("monthly_income", 0),
        existing_emi     = financials.get("existing_emi", 0),
        cibil_score      = financials.get("cibil_score", 700),
        employment_years = financials.get("employment_years", 2),
    )

    pfl_options = calculate_pfl_options(req.loan_amount)

    # Log the application
    log_query(req.session_id, req.user_id, {
        "user_input":  f"Loan application for ₹{req.loan_amount:,}",
        "cost_result": {"total_min": req.loan_amount, "total_max": req.loan_amount,
                        "confidence": 1.0},
        "nodes_visited": ["loan_apply"],
    })

    return {
        "success":      True,
        "decision":     eligibility["decision"],
        "eligibility":  eligibility,
        "pfl_options":  pfl_options,
        "message":      eligibility["recommendation"],
        "sent_to_pfl":  eligibility["decision"] in ["GREEN", "YELLOW"],
        "pfl_contact":  "A Poonawalla Fincorp representative will contact you within 24 hours."
                        if eligibility["decision"] in ["GREEN", "YELLOW"] else None,
    }

# ══════════════════════════════════════════════════════════════════════════════
# RUN SERVER
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)