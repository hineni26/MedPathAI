<div align="center">
<pre>
```
    ███╗░░░███╗███████╗██████╗░██████╗░░█████╗░████████╗██╗░░██╗
    ████╗░████║██╔════╝██╔══██╗██╔══██╗██╔══██╗╚══██╔══╝██║░░██║
    ██╔████╔██║█████╗░░██║░░██║██████╔╝███████║░░░██║░░░███████║
    ██║╚██╔╝██║██╔══╝░░██║░░██║██╔═══╝░██╔══██║░░░██║░░░██╔══██║
    ██║░╚═╝░██║███████╗██████╔╝██║░░░░░██║░░██║░░░██║░░░██║░░██║
    ╚═╝░░░░░╚═╝╚══════╝╚═════╝░╚═╝░░░░░╚═╝░░╚═╝░░░╚═╝░░░╚═╝░░╚═╝
```
</pre>

**AI-Powered Care Navigation & Healthcare Financing for India**

*From first symptom to financing approval — guided by AI, every step of the way.*

![React](https://img.shields.io/badge/React-19-61DAFB?style=flat-square&logo=react)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=flat-square&logo=fastapi)
![LangGraph](https://img.shields.io/badge/LangGraph-0.2.28-4B8BBE?style=flat-square)
![Gemini](https://img.shields.io/badge/Gemini-2.5%20Flash-4285F4?style=flat-square&logo=google)
![Supabase](https://img.shields.io/badge/Supabase-Postgres-3ECF8E?style=flat-square&logo=supabase)

</div>

---

## What is MedPath AI?

MedPath AI is a full-stack conversational healthcare navigation platform built for the Indian market. Describe your symptoms in plain language — the AI figures out what procedure you need, finds the right hospitals in your city, shows a personalised cost breakdown adjusted for your medical history, and walks you through applying for a Poonawalla Fincorp medical loan. All in one chat.

No phone calls. No clinic hopping. No guesswork.

---

## Features

- **Conversational clinical intake** — Gemini 2.5 Flash extracts procedure, city, urgency, and ICD-10 codes from plain language
- **Emergency bypass** — detected at ≥85% confidence, skips clarification entirely and surfaces hospitals immediately with a red alert banner
- **Intelligent hospital ranking** — scored by cost match, quality rating, NABH/JCI accreditation, wait time, and GPS distance
- **Personalised cost breakdowns** — comorbidity multipliers (diabetes, cardiac, kidney, etc.) applied on top of procedure base costs
- **PFL loan pre-qualification** — instant GREEN / YELLOW / RED eligibility decision based on CIBIL, income, FOIR, and loan multiple
- **Gemini document extraction** — upload your salary slip or CIBIL report and the AI fills in your financial profile automatically
- **Real-time loan tracking** — patient app polls loan status every 3 seconds; sees the officer's decision the moment it's made
- **5-step registration wizard** — health profile, comorbidities, insurance, financials, and emergency contact
- **Spectator-safe officer dashboard** — completely separate Vite build for PFL officers; ships zero patient code

### Coming Soon
- **AI second opinion** — challenge a hospital recommendation with a follow-up question
- **User profiles** — persistent health history and past consultation summaries
- **Real PFL API** — live Poonawalla Fincorp loan disbursement integration

---

## Tech Stack

```
┌──────────────────────────────────────────────────────────┐
│                React 19 + Vite (Frontend)                │
│        React Router 7 · Tailwind v4 · Zustand 5          │
└─────────────────────┬────────────────────────────────────┘
                      │ HTTP + REST
         ┌────────────┴────────────┐
         │                         │
┌────────▼────────┐      ┌─────────▼────────────┐
│  FastAPI 0.115  │      │  Supabase (Postgres) │
│  LangGraph      │◀────▶│  + Storage Bucket    │
│  Pipeline       │      │  9 tables            │
└────────┬────────┘      └──────────────────────┘
         │
    ┌────┴──────────────────────────┐
    ▼            ▼                  ▼
 INTENT       PROVIDER           COST + RESPONSE
 Gemini       Pure Python        Formula Engine
 2.5 Flash    Hospital           + Gemini
 Clinical     Scoring            2.5 Flash
 Intake       Engine
```

| Layer | Technology |
|---|---|
| Frontend | React 19, Vite 8, Tailwind CSS v4, React Router 7 |
| State | Zustand 5, custom hooks (useChat, useLoan, useDocuments) |
| Backend | FastAPI 0.115, Uvicorn 0.30, Pydantic v2 |
| AI Pipeline | LangGraph 0.2.28, Gemini 2.5 Flash |
| Clinical Intake | `gemini-2.5-flash` (intent extraction, ICD-10 mapping) |
| Relevance + Scoring | Pure Python, Pandas, Haversine distance |
| Document Extraction | `gemini-2.5-flash` (PDF/image → structured JSON) |
| Database | Supabase Postgres + Supabase Storage |

---

## Getting Started

### Prerequisites
- Node.js 20+
- Python 3.11+
- A Supabase project (free tier works)
- A Google Gemini API key (Gemini 2.5 Flash access required)

### 1. Clone the repo
```bash
git clone https://github.com/yourusername/MedPathAI.git
cd MedPathAI
```

### 2. Backend — Python environment
```bash
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Backend — environment variables
Create a `.env` file inside `backend/` (or copy from `.env.example`):
```env
SUPABASE_URL=https://<your-project>.supabase.co
SUPABASE_KEY=<your-supabase-anon-or-service-key>
GEMINI_API_KEY=<your-gemini-api-key>
DOCUMENT_BUCKET=medical-documents
DOCUMENT_EXTRACTION_ENABLED=false

# JWT Authentication (optional, for production)
JWT_SECRET=<your-secret-key>
JWT_TTL_SECONDS=86400
PFL_OFFICER_API_KEY=<optional-api-key-for-officer-dashboard>
```

### 4. Frontend — environment variables
Create a `.env.local` file inside `medpathai/` (or copy from `.env.example`):
```env
VITE_API_BASE_URL=http://localhost:8000
VITE_SUPABASE_URL=https://<your-project>.supabase.co
VITE_SUPABASE_ANON_KEY=<your-anon-key>
```

### 5. Run the backend
```bash
python ./backend/main.py   # → http://localhost:8000
```

### 6. Frontend
```bash
cd medpathai
npm install
npm run dev         # → http://localhost:5173 (patient app)
npm run dev:pfl     # → http://localhost:5174 (PFL officer dashboard)
```

### 7. Verify everything is running
- `http://localhost:5173` → Patient chat app
- `http://localhost:5174` → PFL officer dashboard
- `http://localhost:8000` → `{"status": "MedPath AI is running :)"}`
- `http://localhost:8000/docs` → FastAPI Swagger UI (test `/api/chat` here)

On first run the backend loads hospital, procedure, and city data from Supabase into memory. Seed CSVs are in `backend/data/`.

---

## Build & Deployment

### Build for production
```bash
# Patient app
cd medpathai && npm run build       # → dist/

# Officer dashboard
cd medpathai && npm run build:pfl   # → dist-pfl/

# Backend is production-ready via Uvicorn
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Deploy to Vercel (frontend)
```bash
vercel deploy
```
Uses `vercel.json` config for SPA routing.

### Deploy to Railway (backend)
```bash
railway link
railway deploy
```
Uses `railway.toml` config for Python FastAPI deployment.

---

## API Endpoints

### Chat & Recommendations
- `POST /api/chat` — Send message, get LangGraph response (intent→provider→cost→response)
- `GET /api/hospitals` — List hospitals for a city
- `GET /api/procedures` — List available procedures

### Registration & Profile
- `POST /api/register` — Create user profile with health details
- `GET /api/profile/{user_id}` — Retrieve user profile
- `PUT /api/profile/{user_id}` — Update profile info

### Loan & Finance
- `POST /api/loan` — Submit PFL loan application (runs eligibility check)
- `GET /api/loan/{loan_id}` — Get loan status
- `PUT /api/loan/{loan_id}/approve` — Officer approves/rejects loan

### Document Processing
- `POST /api/extract-document` — Upload PDF/image, extract via Gemini
- `GET /api/documents/{user_id}` — List user documents

### Security & Auth
- `POST /api/auth/login` — Phone/email authentication
- `POST /api/auth/verify` — OTP verification
- `POST /api/auth/logout` — Clear session

---

## Security Features

The `security.py` module provides:

- **JWT Authentication** — Stateless session tokens with configurable TTL (default: 24 hours)
- **API Key Validation** — PFL officer dashboard is protected by `PFL_OFFICER_API_KEY`
- **HMAC Signatures** — Verify webhook authenticity from Poonawalla Fincorp
- **CORS** — Restricted to frontend domains (`http://localhost:5173` in dev)

**Key functions:**
- `create_jwt(user_id)` — Generate token
- `verify_jwt(token)` — Validate + decode
- `verify_officer_api_key(api_key)` — Check officer access

---

## How It Works

1. Register with your health profile, comorbidities, insurance details, and financials
2. Upload financial documents — salary slip, ITR, CIBIL report (Gemini extracts the data automatically)
3. Open the chat and describe your symptoms or the procedure you need
4. The AI asks up to **3 targeted clarifying questions** — then commits to a recommendation
5. Get a ranked list of hospitals in your city with personalised cost breakdowns
6. Select a hospital and apply for a Poonawalla Fincorp medical loan in one click
7. The AI runs an instant eligibility check and submits your application
8. Track your loan status live — the PFL officer's decision appears in seconds

---

## ML Scoring Pipeline

Every argument — sorry, every *argument* in the chat — runs through four stages in the LangGraph pipeline:

| Node | Model / Engine | Role |
|---|---|---|
| Intent | Gemini 2.5 Flash | Extracts procedure, city, budget, urgency, emergency flag, ICD-10 hint |
| Provider | Pure Python + Pandas | Scores hospitals by cost, quality, accreditation, wait time, GPS distance |
| Cost | Formula Engine | Personalised breakdown with comorbidity multipliers + PFL loan options |
| Response | Gemini 2.5 Flash | Generates warm, clinically-phrased summary or emergency alert |

**Comorbidity multipliers:** Kidney Disease +22% · Cardiac +18% · Diabetes +12% · Obesity +10% · Hypertension +8% · Asthma +6%

**PFL eligibility tiers:** CIBIL ≥700, income ≥₹15k/month, FOIR ≤50%, loan ≤10× income → **GREEN** (instant approval) · soft flags → **YELLOW** · hard failure → **RED** (alternatives suggested)

---

## Project Structure

```
MedPathAI/
├── backend/                        # FastAPI + LangGraph server
│   ├── main.py                     # All HTTP endpoints + CORS + error handling
│   ├── graph.py                    # LangGraph StateGraph (intent→provider→cost→response)
│   ├── loan_engine.py              # PFL credit policy, CIBIL checks, EMI calculations
│   ├── security.py                 # JWT auth, API key validation, signature verification
│   ├── db.py                       # Supabase client, DB helpers, ORM mappings
│   ├── data_loader.py              # Hospital search engine, cost formulas, city lookup
│   ├── test_intent.py              # Manual testing of intent extraction node
│   ├── nodes/
│   │   ├── intent.py               # Gemini clinical intake node (ICD-10 extraction)
│   │   ├── provider.py             # Hospital scoring engine (pure Python + Pandas)
│   │   ├── cost.py                 # Cost breakdown, comorbidity multipliers, loan options
│   │   └── response.py             # Gemini response generation, emergency alerts
│   └── data/                       # Seed CSVs for bootstrap
│       ├── hospitals_rows.csv      # 500+ hospital records
│       ├── procedures_rows.csv     # ICD-10 procedure mappings
│       └── cities_rows.csv         # City location data
│
├── medpathai/                      # React 19 + Vite frontend
│   ├── src/
│   │   ├── App.jsx                 # Main app router (Login → Registration → Chats)
│   │   ├── main.jsx                # Vite entry point (patient app)
│   │   ├── screens/
│   │   │   ├── Chats/              # Main chat interface
│   │   │   │   ├── index.jsx       # Chat container + message management
│   │   │   │   ├── ChatInput.jsx   # Message input + voice support
│   │   │   │   ├── MessageList.jsx # Scrollable message history
│   │   │   │   ├── MessageBubble.jsx  # Styled chat bubbles
│   │   │   │   ├── HospitalCard.jsx   # Hospital recommendation cards
│   │   │   │   ├── CostBreakdown.jsx  # Cost itemization + comorbidity display
│   │   │   │   ├── EligibilityResult.jsx  # PFL loan status (GREEN/YELLOW/RED)
│   │   │   │   ├── PFLLoanPanel.jsx    # Loan application flow
│   │   │   │   ├── ProviderModePanel.jsx  # Hospital provider mode UI
│   │   │   │   └── PossibleCauses.jsx    # Diagnostic suggestions
│   │   │   ├── Documents/          # Document upload + Gemini extraction
│   │   │   │   ├── index.jsx       # Main documents screen
│   │   │   │   ├── UploadDropzone.jsx  # Drag-drop PDF/image uploader
│   │   │   │   ├── DocumentCard.jsx    # Uploaded document preview
│   │   │   │   └── ExtractionPreview.jsx  # Extracted JSON viewer
│   │   │   ├── Registrations/      # 5-step onboarding wizard
│   │   │   │   ├── index.jsx       # Wizard container + step navigation
│   │   │   │   ├── StepHealthProfile.jsx  # Age, gender, allergies
│   │   │   │   ├── StepComorbidities.jsx  # Disease checkboxes (diabetes, etc.)
│   │   │   │   ├── StepInsurance.jsx     # Insurance provider + plan details
│   │   │   │   ├── StepFinancials.jsx    # Income, employment status, FOIR
│   │   │   │   └── StepEmergencyContact.jsx  # Phone + alternate contact
│   │   │   ├── LoanHistory/        # Loan application tracking
│   │   │   │   └── index.jsx       # Tabular view with status badges
│   │   │   ├── Login/              # Auth entry point
│   │   │   │   └── index.jsx       # Phone/email login form
│   │   │   └── PFLDashboard/       # (Officer dashboard - see officer/ build)
│   │   │       └── index.jsx       # Loan applications review interface
│   │   ├── components/             # Shared UI components
│   │   │   ├── AppShell.jsx        # Layout wrapper (sidebar + content)
│   │   │   ├── Sidebar.jsx         # Navigation menu + user profile
│   │   │   ├── Topbar.jsx          # Header with title + actions
│   │   │   ├── EmergencyBanner.jsx # Red alert for emergency cases
│   │   │   ├── Modal.jsx           # Generic modal dialog
│   │   │   ├── StepIndicator.jsx   # Registration wizard step tracker
│   │   │   └── ui.jsx              # Reusable UI primitives (Button, Input, etc.)
│   │   ├── hooks/                  # Custom React hooks
│   │   │   ├── useChat.js          # Chat state + message management
│   │   │   ├── useLoan.js          # Loan application state + tracking
│   │   │   ├── useDocuments.js     # Document upload + extraction state
│   │   │   ├── useGeolocation.js   # GPS coordinates (hospital distance)
│   │   │   └── useProfile.js       # User registration + profile state
│   │   ├── store/                  # Zustand state management
│   │   │   ├── chatStore.js        # Chat messages, responses, hospital data
│   │   │   ├── userStore.js        # User profile, health, financials, documents
│   │   │   └── uiStore.js          # UI state, toast notifications, modals
│   │   ├── api/                    # Axios API client helpers
│   │   │   ├── client.js           # Axios instance with auth headers
│   │   │   ├── chat.js             # POST /api/chat endpoint
│   │   │   ├── auth.js             # Auth helpers (getUserId, isRegistered)
│   │   │   ├── session.js          # JWT + localStorage management
│   │   │   ├── registration.js     # POST/GET registration profile
│   │   │   ├── loan.js             # POST /api/loan (PFL application)
│   │   │   ├── documents.js        # POST /api/extract-document
│   │   │   ├── financials.js       # Financials API helpers
│   │   │   └── pfl.js              # PFL officer status checks
│   │   ├── utils/                  # Helper utilities
│   │   │   ├── helpers.js          # Date, string, array utilities
│   │   │   ├── formatCurrency.js   # ₹ formatting + locale
│   │   │   └── staticData.js       # Constants, enums, lookup tables
│   │   ├── styles/                 # Global CSS / Tailwind overrides
│   │   └── index.html              # HTML template (patient app)
│   ├── officer/                    # PFL officer dashboard (separate Vite build)
│   │   ├── main.jsx                # Officer app entry point
│   │   └── index.html              # Officer app HTML template
│   ├── dist/                       # Built patient app (npm run build)
│   ├── dist-pfl/                   # Built officer app (npm run build:pfl)
│   ├── vite.config.js              # Patient app Vite config (port 5173)
│   ├── vite.pfl.config.js          # Officer app Vite config (port 5174)
│   ├── eslint.config.js            # ESLint rules
│   ├── vercel.json                 # Vercel deployment config (SPA routing)
│   ├── package.json                # Dependencies + build scripts
│   ├── package-lock.json           # Lock file
│   └── README.md                   # Frontend-specific docs
│
├── railway.toml                    # Railway.app deployment config
└── requirements.txt                # Python backend dependencies
```

---

## Testing & Debugging

### Test Intent Extraction
```bash
cd backend
python test_intent.py
```
Directly test the Gemini intent extraction node with sample symptoms.

### View API Docs
- FastAPI Swagger UI: `http://localhost:8000/docs`
- FastAPI ReDoc: `http://localhost:8000/redoc`

### Debug Mode
Add to `.env`:
```env
DEBUG=true
LOG_LEVEL=DEBUG
```

### Common Issues

**"Supabase connection failed"**
- Check `SUPABASE_URL` and `SUPABASE_KEY` in `.env`
- Verify your Supabase project is active

**"Gemini API key invalid"**
- Ensure `GEMINI_API_KEY` is set and has access to Gemini 2.5 Flash model
- Check API quotas in Google Cloud console

**"Hospital data not loading"**
- Ensure CSVs exist in `backend/data/`
- Check Supabase tables are seeded: `users`, `hospitals`, `procedures`, `cities`

**Frontend won't connect to backend**
- Verify backend is running on `http://localhost:8000`
- Check `VITE_API_BASE_URL` in `.env.local`
- Browser console should show no CORS errors

---

## Database Schema

Key Supabase tables:

| Table | Columns | Purpose |
|---|---|---|
| `users` | id, phone, email, profile_json, created_at | User accounts + profiles |
| `hospitals` | id, name, city, rating, nabh_accred, procedures | Hospital directory |
| `procedures` | id, icd10_code, name, base_cost, avg_cost | Procedure catalog |
| `cities` | id, name, latitude, longitude | City location data |
| `loans` | id, user_id, amount, status, cibil_score | Loan applications |
| `documents` | id, user_id, type, url, extracted_json | Uploaded PDFs + extraction |
| `chats` | id, user_id, intent, response_json, timestamp | Chat history |

---

## Roadmap

- [x] Conversational AI intake via LangGraph + Gemini
- [x] Hospital discovery + multi-factor scoring
- [x] Personalised cost breakdowns with comorbidity multipliers
- [x] PFL medical loan pre-qualification engine
- [x] Gemini-powered document extraction
- [x] Real-time loan status tracking
- [x] PFL officer approval dashboard (separate build)
- [x] Emergency detection + bypass flow
- [x] 5-step registration wizard
- [x] Admin analytics dashboard
- [ ] AI second opinion mode
- [ ] User profile settings screen
- [ ] Real Poonawalla Fincorp API integration

---

<div align="center">
  <sub>Built by Team NightLamps</sub>
</div>