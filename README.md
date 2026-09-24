# Voice AI Agent - Patient Registration System

## Overview

A voice-based AI patient registration system that collects U.S. patient demographic information through natural voice conversation, persists data to a database, and exposes it via a REST API.

## Architecture

```
Phone Call (Caller)
       ↕
   Vapi (Voice AI Platform)
       ↕ (HTTP API calls)
   FastAPI Backend (This project)
       ↕
   Supabase (Database + Auth)
```

### Layers

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Telephony/Voice AI** | Vapi | Handles phone calls, STT/TTS, and LLM conversation |
| **Backend API** | FastAPI (Python) | REST API for patient CRUD operations |
| **Database** | Supabase (PostgreSQL) | Persistent patient records |
| **Voice Model** | OpenAI GPT-4o-mini | Natural language understanding and generation |
| **STT/TTS** | Deepgram / ElevenLabs | Speech-to-text and text-to-speech |

---

## Project Structure

```
patient-registration/
│
├── api/
│   └── .env                      # Environment variables (Supabase, Vapi, etc.)
├── app/
│   ├── __init__.py
│   ├── main.py                   # FastAPI app initialization and server runner
│   ├── config.py                 # Environment configuration and constants
│   ├── models/
│   │   ├── __init__.py
│   │   └── patient.py            # Pydantic schemas (PatientCreate, PatientUpdate, PhoneCheck)
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── patient.py            # Patient CRUD endpoints
│   │   ├── webhook.py            # Vapi voice agent webhook handler
│   │   └── dashboard.py          # HTML dashboard route
│   ├── services/
│   │   ├── __init__.py
│   │   └── supabase.py           # Supabase client initialization
│   └── utils/
│       ├── __init__.py
│       └── helpers.py            # Helper functions (now_utc, error_response, serialize_row)
├── venv/
├── requirements.txt
├── schema.sql
├── vercel.json
├── README.md
└── .gitignore
```

### File Purpose Reference

| File | Purpose |
|------|---------|
| `app/main.py` | **App entry point.** FastAPI app initialization, health check, exception handler, and router registration. Runs uvicorn on port 8000 when executed directly. |
| `app/config.py` | **Configuration.** Loads environment variables from `api/.env`, defines `SUPABASE_URL`, `US_STATE_ABBR`, and other constants. |
| `app/models/patient.py` | **Pydantic schemas.** `PatientCreate`, `PatientUpdate`, `PhoneCheck` models with full validation (names, state, ZIP, phone, DOB). |
| `app/routes/patient.py` | **Patient CRUD.** All patient endpoints (`/patients`, `/patients/:id`, `/patients/check-phone`) with duplicate detection. |
| `app/routes/webhook.py` | **Vapi webhook.** Handles incoming webhook calls from Vapi (`/vapi-webhook`) for `checkExistingPatient`, `registerPatient`, `updatePatient`, etc. |
| `app/routes/dashboard.py` | **Dashboard.** Renders HTML table of all registered patients at `/dashboard`. |
| `app/services/supabase.py` | **Supabase client.** Initializes and exports the Supabase client instance. |
| `app/utils/helpers.py` | **Utilities.** `now_utc()`, `error_response()`, `success_response()`, `serialize_row()`. |
| `requirements.txt` | Lists all Python packages needed to run the project. |
| `schema.sql` | SQL script to create the `patients` table, indexes, triggers, and seed data in Supabase. |
| `vercel.json` | Tells Vercel how to build and deploy the application. |
| `.gitignore` | Prevents sensitive files (`api/.env`, `venv/`, `__pycache__/`) from being committed to Git. |

---

## Quick Start

### Prerequisites

- Python 3.11+
- Supabase project with credentials
- Vapi API key
- `api/.env` file configured

### Setup Instructions

1. **Clone the repository**
   ```bash
   git clone <repo-url>
   cd patient-registration
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   venv\Scripts\activate  # On Windows
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up Supabase Database**
   - Run `schema.sql` in your Supabase SQL editor to create the `patients` table, indexes, triggers, and seed data.

5. **Configure environment variables**
   - Edit `api/.env` with your Supabase URL, service role key, and Vapi API key.
   - **Important**: `SUPABASE_URL` should be `https://zjmsaiqztajzfclishnk.supabase.co` (without `/rest/v1/`).

6. **Run the server locally**
     ```bash
     python -m app.main
     ```
     The API will be available at `http://localhost:8000`.

7. **Test the API**
   - Health check: `http://localhost:8000/`
   - List patients: `http://localhost:8000/patients`
   - Dashboard: `http://localhost:8000/dashboard`

8. **Configure Vapi Assistant** ✅
    - Vapi API key configured in `api/.env`
    - **Model**: OpenAI GPT-4o-mini
    - **Voice**: Alloy
    - **System Prompt**: Natural conversational flow for patient registration
    - **Staff Phone**: `+1 (463) 223 1070`
    - Provisioned a phone number in Vapi.

---

## Running the Project

### Local Development

```bash
# Activate virtual environment
venv\Scripts\activate

# Run the server
python -m app.main
```

The server starts with hot-reload on `http://localhost:8000`. All endpoints are available at this address.

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Health check |
| `GET` | `/dashboard` | Web dashboard for viewing all patients |
| `GET` | `/patients` | List all patients (supports `?last_name=`, `?date_of_birth=`, `?phone_number=`) |
| `GET` | `/patients/:id` | Get single patient by UUID |
| `POST` | `/patients` | Create new patient (checks for duplicate phone) |
| `PUT` | `/patients/:id` | Update existing patient (partial updates) |
| `DELETE` | `/patients/:id` | Delete patient |
| `POST` | `/patients/check-phone` | Check if phone number is a duplicate |
| `POST` | `/vapi-webhook` | Vapi voice agent webhook |

### Response Format

All responses follow the consistent envelope:
```json
{ "data": {...}, "error": null }
```

### HTTP Status Codes

- `200` - Success
- `201` - Resource created
- `400` - Bad request
- `404` - Not found
- `409` - Duplicate conflict
- `422` - Validation error
- `500` - Internal server error

---

## Deployment

This project is deployed on Vercel.

### Deployed App

The application is live at: `https://your-app.vercel.app`

### Deploy to Vercel

1. Push code to GitHub/GitLab
2. Go to [vercel.com](https://vercel.com) and create a new project
3. Import your repository
4. Add environment variables:
    - `SUPABASE_URL`
    - `SUPABASE_SERVICE_ROLE_KEY`
    - `VAPI_API_KEY`
    - `BASE_URL`
    - `STAFF_PHONE`
5. Click **Deploy**
6. Vercel automatically detects `requirements.txt` and `vercel.json`

---

## Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `SUPABASE_URL` | Supabase project URL (no trailing `/rest/v1/`) | `https://zjmsaiqztajzfclishnk.supabase.co` |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase service role key (admin) | `sb_secret_...` |
| `VAPI_API_KEY` | Vapi platform API key | `8de0284f-...` |
| `BASE_URL` | Base URL of the deployed API (used by Vapi) | `https://your-app.vercel.app` |
| `STAFF_PHONE` | Staff phone for transfers | `+1 (463) 223 1070` |

---

## Vapi Assistant Configuration ✅

The Vapi assistant is **configured and ready** with:

- **Model**: OpenAI GPT-4o-mini
- **Voice**: Alloy
- **System Prompt**: Natural conversational flow for patient registration
- **API Key**: Configured in `api/.env` (`VAPI_API_KEY`)
- **Staff Phone**: `+1 (463) 223 1070`

The assistant:
1. Greets callers and collects required demographics
2. Offers optional fields (insurance, emergency contact, language)
3. Checks for duplicate phone numbers
4. Confirms all information before saving
5. Provides success confirmation or error messages

---

## Validation Rules

| Field | Rule |
|-------|------|
| `first_name`, `last_name` | 1-50 chars, alphabetic + hyphens/apostrophes |
| `date_of_birth` | Valid date in MM/DD/YYYY, not in future |
| `sex` | Male, Female, Other, Decline to Answer |
| `phone_number` | Valid 10-digit US phone number |
| `state` | Valid 2-letter US state abbreviation |
| `zip_code` | 5-digit or ZIP+4 format |
| `email` | Valid email format |

---

## Observability

All agent conversations and registration events are logged to stdout:
```
[VOICE AGENT] New patient registered: Jane Doe (ID: a1b2c3d4-...)
```

---

## Known Limitations / Trade-offs

- **Development mode**: Local development uses `uvicorn` for hot-reload. For production, serverless deployment via Vercel.
- **RLS**: Row Level Security is enabled but the service role key bypasses it. In production, consider using the anon key with proper policies.
- **No async processing**: Phone call webhooks are handled synchronously. For high call volumes, consider an async task queue.

---

## Next Steps

- [x] Configure Vapi assistant with API key and phone number
- [x] Provision a phone number in Vapi
- [ ] Set `BASE_URL` to deployed API URL in Vapi
- [ ] Apply `schema.sql` to Supabase database
- [ ] Add unit tests for API endpoints
- [ ] Add appointment scheduling after registration
- [ ] Add multi-language support (Spanish)
- [ ] Add call transcript storage
- [ ] Create simple web dashboard for viewing patients
- [ ] Add automated test suite

---

## License

CONFIDENTIAL - For Candidate Use Only
