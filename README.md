# Patient Registration System — Voice AI Agent

A voice-powered patient registration system built with **Vapi**, **FastAPI**, and **Supabase**. Patients can be registered, updated, and queried via voice conversation through Vapi's AI agent.

## Features

- **Voice-Driven Registration** — Register patients by speaking with an AI agent via Vapi
- **Full CRUD Operations** — Create, Read, Update, Delete patient records
- **Supabase Backend** — Persistent storage with real-time database
- **Vapi Webhook Integration** — AI agent calls tools to interact with the system
- **Dashboard** — Web UI to view all registered patients
- **Phone Duplicate Check** — Prevent duplicate patient entries

## Tech Stack

- **FastAPI** — Python web framework for REST API and webhook handling
- **Supabase** — PostgreSQL database with real-time capabilities
- **Vapi** — Voice AI platform for conversational agent
- **Vercel** — Cloud deployment platform
- **Python-dotenv** — Environment variable management

## Project Structure

```
patient-registration/
├── api/
│   ├── index.py          # Vercel entry point (imports app from main)
│   └── main.py           # FastAPI application with all routes & webhook
├── .env.local            # Local environment variables (not committed)
├── .gitignore
├── vercel.json           # Vercel deployment configuration
├── requirements.txt      # Python dependencies
├── venv/                 # Python virtual environment
└── README.md
```

## Setup

### Prerequisites

- Python 3.11+
- A Supabase project
- A Vapi account
- A Vercel account

### Environment Variables

Create a `.env.local` file in the project root:

```env
SUPABASE_URL=https://your-project.supabase.co/rest/v1/
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
VAPI_API_KEY=your-vapi-api-key
STAFF_PHONE=+1XXXXXXXXXX
```

### Local Development

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the server
python api/main.py
```

The API will be available at `http://localhost:8000`.

## Vercel Deployment

1. Push the code to GitHub
2. Import the repository in Vercel
3. Add environment variables in **Project Settings → Environment Variables**:
   - `SUPABASE_URL`
   - `SUPABASE_SERVICE_ROLE_KEY`
   - `VAPI_API_KEY`
4. Vercel auto-deploys on every `git push`

## Vapi Configuration

### Webhook URL
```
https://patient-registration-system-one.vercel.app/vapi-webhook
```

### Tools (Function Calls)

| Function Name | Action | Description |
|---|---|---|
| `checkExistingPatient` | READ | Check if a patient exists by phone number |
| `registerPatient` | WRITE | Register a new patient with full details |
| `updatePatient` | UPDATE | Update existing patient information |
| `checkAvailability` | READ | Check appointment availability |
| `bookAppointment` | WRITE | Book a new appointment |
| `sendSms` | WRITE | Send SMS notification |
| `transferCall` | OTHER | Transfer call to staff |

### Vapi Dashboard Setup

1. Go to [Vapi Dashboard](https://vapi.ai)
2. Create a new assistant
3. Set **Webhook URL** to `https://patient-registration-system-one.vercel.app/vapi-webhook`
4. Add tools matching the function names above
5. Configure the system prompt to instruct the AI when to use each tool

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Health check |
| `GET` | `/patients` | List all patients (filter by last_name, date_of_birth, phone_number) |
| `GET` | `/patients/{patient_id}` | Get single patient by ID |
| `POST` | `/patients` | Create new patient |
| `PUT` | `/patients/{patient_id}` | Update patient |
| `DELETE` | `/patients/{patient_id}` | Delete patient |
| `POST` | `/patients/check-phone` | Check if phone number already exists |
| `POST` | `/vapi-webhook` | Vapi webhook for AI agent tool calls |
| `GET` | `/dashboard` | Web dashboard with all patients |

## Database Schema (Supabase `patients` table)

| Column | Type | Description |
|---|---|---|
| `patient_id` | UUID | Primary key |
| `first_name` | TEXT | Patient first name |
| `last_name` | TEXT | Patient last name |
| `date_of_birth` | TEXT | Date of birth (YYYY-MM-DD) |
| `sex` | TEXT | Male / Female / Other |
| `phone_number` | TEXT | 10-digit phone number |
| `address_line_1` | TEXT | Street address |
| `city` | TEXT | City |
| `state` | TEXT | 2-letter state abbreviation |
| `zip_code` | TEXT | ZIP code |
| `email` | TEXT | Email (optional) |
| `address_line_2` | TEXT | Address line 2 (optional) |
| `insurance_provider` | TEXT | Insurance provider (optional) |
| `insurance_member_id` | TEXT | Member ID (optional) |
| `preferred_language` | TEXT | Preferred language |
| `emergency_contact_name` | TEXT | Emergency contact name (optional) |
| `emergency_contact_phone` | TEXT | Emergency contact phone (optional) |
| `created_at` | TIMESTAMPTZ | Record creation timestamp |
| `updated_at` | TIMESTAMPTZ | Last update timestamp |
| `deleted_at` | TIMESTAMPTZ | Soft delete timestamp |

## License

MIT
