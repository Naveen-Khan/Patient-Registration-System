# Voice AI Agent - Patient Registration System

## Overview


A production-oriented Voice AI agent that handles inbound patient registration calls for "Meridian Health Clinic". The AI agent ("Naveen") conducts a natural, conversational intake process, collects all required U.S. demographic data, confirms the information, and persists it to a Supabase (PostgreSQL) database. A companion REST API is exposed for querying and managing patient records.

## Architecture

```
Phone Call (Caller)
       ↕
   Vapi (Voice AI Platform)
       ↕ (HTTP API calls)
   FastAPI Backend (This project)
       ↕
   Supabase (Database )
```

### Layers

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Telephony/Voice AI** | Vapi | Handles phone calls, STT/TTS, and LLM conversation |
| **Backend API** | FastAPI (Python) | REST API for patient CRUD operations |
| **Database** | Supabase (PostgreSQL) | Persistent patient records with UUID, soft-delete |
| **Voice Model** | OpenAI GPT-4o-mini | Natural language understanding and generation |
| **STT/TTS** | Elliot  Speech-to-text and text-to-speech |

## Tech Stack and Justification
*Voice AI and Telephony:* Vapi.ai - Abstracts the complexity of stitching STT, TTS, and LLMs. It handles telephony provisioning and tool-calling natively, saving hours of infrastructure setup.
*Backend: Python (FastAPI)* - Chosen for its asynchronous capabilities and robust Pydantic data validation. FastAPI ensures that unstructured LLM outputs are strictly validated before hitting the database.
*Database: Supabase (PostgreSQL) *- Chosen for its reliability, strong typing, and built-in row-level security. Supabase allows the application of strict schema constraints (regex, enums) at the database level, ensuring zero bad data enters the system.
*Hosting:* Vercel - Used for seamless serverless deployment of the FastAPI backend. It provides a persistent, HTTPS-secured URL required by Vapi webhook
### Prerequisites

- Python 3.11+
- Supabase project with credentials
- Vapi API key
- `.env` file configured

### Setup Instructions

1. **Clone the repository**
    ```bash
    git clone <repo-url>
    cd patient-registration
    ```

2. **Create virtual environment**
    ```bash
    python -m venv venv
    source venv/Scripts/activate  # On Windows: venv\Scripts\activate
    ```

3. **Install dependencies**
    ```bash
    pip install -r requirements.txt
    ```

4. **Set up Supabase Database**
    - Run `schema.sql` in your Supabase SQL editor to create the `patients` table, indexes, triggers, and seed data.

5. **Configure environment variables**
    - Edit `.env` with your Supabase URL, service role key, and Vapi API key.

6. **Run the server locally**
    ```bash
    python main.py
    ```
    The API will be available at `http://localhost:8000`.

7. **Configure Vapi Assistant**
    - Import `vapi_assistant.json` into the Vapi dashboard.
    - Set `BASE_URL` to your deployed API URL (e.g., `https://your-app.railway.app`).
    - Provision a phone number in Vapi.

## Deployment

### Deploy to Vercel

This project is configured for Vercel deployment:

1. **Install Vercel CLI**
    ```bash
    npm install -g vercel
    ```

2. **Login to Vercel**
    ```bash
    vercel login
    ```

3. **Set environment variables on Vercel**
    ```bash
    vercel env add SUPABASE_URL
    vercel env add SUPABASE_SERVICE_ROLE_KEY
    vercel env add VAPI_API_KEY
    vercel env add BASE_URL
    vercel env add STAFF_PHONE
    ```

4. **Deploy**
    ```bash
    vercel --prod
    ```

5. **After deployment**, note the URL (e.g., `https://your-app.vercel.app`) and set it as `BASE_URL` in Vercel environment variables. Then configure the Vapi assistant to use this URL.

### Deploy to Railway

1. Push code to GitHub/GitLab
2. Go to [Railway.app](https://railway.app) and create a new project
3. Link your GitHub repository
4. Add environment variables from `.env`
5. Deploy — Railway will detect `requirements.txt` and `main.py`

### Deploy to Render

1. Push code to GitHub/GitLab
2. Go to [Render.com](https://render.com) and create a new Web Service
3. Connect your repository
4. Set build command: `pip install -r requirements.txt`
5. Set start command: `python main.py`
6. Add environment variables from `.env`
7. Deploy

## Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `SUPABASE_URL` | Supabase project URL | `https://zjmsaiqztajzfclishnk.supabase.co/rest/v1/` |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase service role key (admin) | `sb_secret_...` |
| `VAPI_API_KEY` | Vapi platform API key | `8de0284f-...` |
| `BASE_URL` | Base URL of the deployed API (used by Vapi) | `https://your-app.railway.app` |
| `STAFF_PHONE` | Staff phone for transfers | `+1 (463) 223 1070` |

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Health check |
| `GET` | `/patients` | List all patients (supports `?last_name=`, `?date_of_birth=`, `?phone_number=`) |
| `GET` | `/patients/:id` | Get single patient by UUID |
| `POST` | `/patients` | Create new patient (checks for duplicate phone) |
| `PUT` | `/patients/:id` | Update existing patient (partial updates) |
| `DELETE` | `/patients/:id` | Soft-delete patient (sets `deleted_at`) |
| `POST` | `/patients/check-phone` | Check if phone number is a duplicate |

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

## Vapi Assistant Configuration

The Vapi assistant is configured in `vapi_assistant.json` with:

- **Model**: OpenAI GPT-4o-mini
- **Voice**: Alloy
- **Tools**: `check_phone_duplicate`, `create_patient`, `update_patient`
- **System Prompt**: Natural conversational flow for patient registration

The assistant:
1. Greets callers and collects required demographics
2. Offers optional fields (insurance, emergency contact, language)
3. Checks for duplicate phone numbers
4. Confirms all information before saving
5. Provides success confirmation or error messages

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

## Observability

All agent conversations and registration events are logged to stdout:
```
[VOICE AGENT] New patient registered: Jane Doe (ID: a1b2c3d4-...)
```

## Known Limitations / Trade-offs

- **Development mode**: Currently designed for local development with ngrok for Vapi webhook access. For production, deploy to Railway/Render/Fly.io.
- **RLS**: Row Level Security is enabled but the service role key bypasses it. In production, consider using the anon key with proper policies.
- **No async processing**: Phone call webhooks are handled synchronously. For high call volumes, consider an async task queue.
- **Soft-delete only**: Deleted records are marked but not permanently removed. Consider a cleanup job for compliance.

## Next Steps

- [x] Deploy to Vercel
- [ ] Configure Vapi assistant with deployed BASE_URL
- [ ] Provision a phone number in Vapi
- [ ] Add unit tests for API endpoints
- [ ] Add appointment scheduling after registration
- [ ] Add multi-language support (Spanish)
- [ ] Add call transcript storage
- [ ] Create simple web dashboard for viewing patients
- [ ] Add automated test suite

## Vapi Connection Guide

To connect this backend to Vapi:

1. **Deploy the backend** to Vercel (or Railway/Render)
2. **Note the deployed URL** (e.g., `https://your-app.vercel.app`)
3. **Set `BASE_URL`** to the deployed URL in your `.env` file
4. **In Vapi Dashboard**:
   - Create a new Assistant
   - Use the system prompt from `vapi_assistant.json`
   - Add the 3 tools (`check_phone_duplicate`, `create_patient`, `update_patient`) with endpoints pointing to `{BASE_URL}/patients/...`
   - Set the model to `gpt-4o-mini`
   - Set STT to Deepgram and TTS to ElevenLabs
   - Select a voice (e.g., Alloy)
5. **Provision a phone number** in Vapi
6. **Test** by calling the number and going through patient registration

## License

CONFIDENTIAL - For Candidate Use Only
