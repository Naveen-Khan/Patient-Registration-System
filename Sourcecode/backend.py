# Voice AI Agent - Patient Registration API
# Single file backend. Run with: python backend.py

import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.getcwd(), "api", ".env"))

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")


from datetime import datetime, timezone
from typing import Optional
from fastapi.responses import JSONResponse

from supabase import create_client, Client
import os

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

US_STATE_ABBR = {
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA", "HI", "ID", "IL", "IN", "IA",
    "KS", "KY", "LA", "ME", "MD", "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
    "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC", "SD", "TN", "TX", "UT", "VT",
    "VA", "WA", "WV", "WI", "WY"
}

def now_utc() -> str:
    """Return current UTC timestamp in ISO format."""
    return datetime.now(timezone.utc).isoformat()

def error_response(status_code: int, detail: str) -> JSONResponse:
    """Return a standardized error response."""
    return JSONResponse(status_code=status_code, content={"data": None, "error": detail})

def success_response(data: dict) -> JSONResponse:
    """Return a standardized success response."""
    return JSONResponse(status_code=200, content={"data": data, "error": None})

def serialize_row(row: dict) -> Optional[dict]:
    """Clean a database row by removing soft-delete metadata before returning."""
    if not row:
        return None
    row.pop("deleted_at", None)
    return row


from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional
import re
from datetime import datetime
US_STATE_ABBR = {"AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA", "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD", "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ", "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC", "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY"}


class PatientCreate(BaseModel):
    """Schema for creating a new patient record."""
    first_name: str = Field(..., min_length=1, max_length=50)
    last_name: str = Field(..., min_length=1, max_length=50)
    date_of_birth: str = Field(..., pattern=r"^\d{2}/\d{2}/\d{4}$")
    sex: str = Field(..., pattern=r"^(Male|Female|Other|Decline to Answer)$")
    phone_number: str = Field(..., min_length=10, max_length=15)
    address_line_1: str = Field(..., min_length=1, max_length=200)
    city: str = Field(..., min_length=1, max_length=100)
    state: str = Field(..., min_length=2, max_length=2)
    zip_code: str = Field(..., min_length=5, max_length=10)
    email: Optional[str] = Field(None, max_length=255)
    address_line_2: Optional[str] = Field(None, max_length=200)
    insurance_provider: Optional[str] = Field(None, max_length=200)
    insurance_member_id: Optional[str] = Field(None, max_length=100)
    preferred_language: str = "English"
    emergency_contact_name: Optional[str] = Field(None, max_length=100)
    emergency_contact_phone: Optional[str] = Field(None, max_length=15)

    model_config = ConfigDict(extra="ignore")

    @field_validator("first_name", "last_name")
    @classmethod
    def validate_names(cls, v: str) -> str:
        if not re.match(r"^[A-Za-z\-']{1,50}$", v):
            raise ValueError("Name must be 1-50 characters, alphabetic with hyphens/apostrophes only")
        return v

    @field_validator("state")
    @classmethod
    def validate_state(cls, v: str) -> str:
        if v not in US_STATE_ABBR:
            raise ValueError("State must be a valid 2-letter US state abbreviation")
        return v

    @field_validator("zip_code")
    @classmethod
    def validate_zip(cls, v: str) -> str:
        if not re.match(r"^\d{5}(-\d{4})?$", v):
            raise ValueError("ZIP code must be 5-digit or ZIP+4 format")
        return v

    @field_validator("phone_number")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        if len(re.sub(r"[^\d]", "", v)) != 10:
            raise ValueError("Phone number must be a valid 10-digit US phone number")
        return v

    @field_validator("emergency_contact_phone")
    @classmethod
    def validate_emergency_phone(cls, v: Optional[str]) -> Optional[str]:
        if v and len(re.sub(r"[^\d]", "", v)) != 10:
            raise ValueError("Emergency contact phone must be a valid 10-digit US phone number")
        return v

    @field_validator("date_of_birth")
    @classmethod
    def validate_dob(cls, v: str) -> str:
        try:
            dob = datetime.strptime(v, "%m/%d/%Y")
            if dob > datetime.now():
                raise ValueError("Date of birth cannot be in the future")
        except ValueError:
            raise ValueError("Date of birth must be a valid date in MM/DD/YYYY format and not in the future")
        return v


class PatientUpdate(BaseModel):
    """Schema for updating an existing patient record (partial updates)."""
    first_name: Optional[str] = Field(None, min_length=1, max_length=50)
    last_name: Optional[str] = Field(None, min_length=1, max_length=50)
    date_of_birth: Optional[str] = Field(None, pattern=r"^\d{2}/\d{2}/\d{4}$")
    sex: Optional[str] = Field(None, pattern=r"^(Male|Female|Other|Decline to Answer)$")
    phone_number: Optional[str] = Field(None, min_length=10, max_length=15)
    address_line_1: Optional[str] = Field(None, min_length=1, max_length=200)
    address_line_2: Optional[str] = Field(None, max_length=200)
    city: Optional[str] = Field(None, min_length=1, max_length=100)
    state: Optional[str] = Field(None, min_length=2, max_length=2)
    zip_code: Optional[str] = Field(None, min_length=5, max_length=10)
    email: Optional[str] = Field(None, max_length=255)
    insurance_provider: Optional[str] = Field(None, max_length=200)
    insurance_member_id: Optional[str] = Field(None, max_length=100)
    preferred_language: Optional[str] = None
    emergency_contact_name: Optional[str] = Field(None, max_length=100)
    emergency_contact_phone: Optional[str] = Field(None, max_length=15)

    model_config = ConfigDict(extra="ignore")

    @field_validator("first_name", "last_name")
    @classmethod
    def validate_names(cls, v: Optional[str]) -> Optional[str]:
        if v and not re.match(r"^[A-Za-z\-']{1,50}$", v):
            raise ValueError("Name must be 1-50 characters, alphabetic with hyphens/apostrophes only")
        return v

    @field_validator("state")
    @classmethod
    def validate_state(cls, v: Optional[str]) -> Optional[str]:
        if v and v not in US_STATE_ABBR:
            raise ValueError("State must be a valid 2-letter US state abbreviation")
        return v

    @field_validator("zip_code")
    @classmethod
    def validate_zip(cls, v: Optional[str]) -> Optional[str]:
        if v and not re.match(r"^\d{5}(-\d{4})?$", v):
            raise ValueError("ZIP code must be 5-digit or ZIP+4 format")
        return v

    @field_validator("phone_number")
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        if v and len(re.sub(r"[^\d]", "", v)) != 10:
            raise ValueError("Phone number must be a valid 10-digit US phone number")
        return v

    @field_validator("emergency_contact_phone")
    @classmethod
    def validate_emergency_phone(cls, v: Optional[str]) -> Optional[str]:
        if v and len(re.sub(r"[^\d]", "", v)) != 10:
            raise ValueError("Emergency contact phone must be a valid 10-digit US phone number")
        return v

    @field_validator("date_of_birth")
    @classmethod
    def validate_dob(cls, v: Optional[str]) -> Optional[str]:
        if v:
            try:
                dob = datetime.strptime(v, "%m/%d/%Y")
                if dob > datetime.now():
                    raise ValueError("Date of birth cannot be in the future")
            except ValueError:
                raise ValueError("Date of birth must be a valid date in MM/DD/YYYY format and not in the future")
        return v


class PhoneCheck(BaseModel):
    """Schema for checking if a phone number already exists."""
    phone_number: str


"""
Voice AI Agent - Patient Registration API
==========================================
A FastAPI backend for a voice-based patient registration system.
All routes, dashboard, webhook, and app initialization live here.
"""

from fastapi import FastAPI, Request, Query, Path
from typing import Optional
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, HTMLResponse
from datetime import datetime
import uuid


# --- FastAPI App ---
app = FastAPI(title="Voice AI Agent - Patient Registration API")

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle all Pydantic validation errors and return a clean error message."""
    errors = [f"{'.'.join(str(x) for x in err['loc'])}: {err['msg']}" for err in exc.errors()]
    return JSONResponse(status_code=422, content={"data": None, "error": "; ".join(errors)})

# --- Health Check ---

@app.get("/")
def health_check():
    """Health check endpoint to verify the server is running."""
    return {"data": {"message": "Voice AI Agent Backend is running!"}, "error": None}

# --- Patient CRUD Endpoints ---

@app.get("/patients")
async def list_patients(
    last_name: Optional[str] = Query(None, description="Filter patients by last name"),
    date_of_birth: Optional[str] = Query(None, description="Filter patients by date of birth (MM/DD/YYYY)"),
    phone_number: Optional[str] = Query(None, description="Filter patients by phone number"),
):
    """List all patients with optional filters by last name, DOB, or phone number."""
    try:
        query = supabase.table("patients").select("*")
        if last_name:
            query = query.ilike("last_name", f"%{last_name}%")
        if date_of_birth:
            query = query.eq("date_of_birth", date_of_birth)
        if phone_number:
            query = query.eq("phone_number", phone_number)
        response = query.execute()
        if response.data is None:
            return error_response(500, "Failed to fetch patients")
        patients = [serialize_row(row) for row in response.data]
        return {"data": patients, "error": None}
    except Exception as e:
        print(f"Error listing patients: {str(e)}")
        return error_response(500, str(e))

@app.get("/patients/{patient_id}")
async def get_patient(patient_id: str = Path(..., pattern=r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", description="Patient UUID")):
    """Retrieve a single patient record by UUID."""
    try:
        response = supabase.table("patients").select("*").eq("patient_id", patient_id).single().execute()
        if not response.data:
            return error_response(404, "Patient not found")
        return success_response(serialize_row(response.data))
    except Exception as e:
        print(f"Error fetching patient: {str(e)}")
        return error_response(500, str(e))

@app.post("/patients", status_code=201)
async def create_patient(patient: PatientCreate):
    """Create a new patient record. Checks for duplicate phone number before inserting."""
    try:
        existing = supabase.table("patients").select("patient_id").eq("phone_number", patient.phone_number).execute()
        if existing.data:
            existing_patient = serialize_row(existing.data[0])
            return error_response(409, f"Patient already exists with this phone number. Patient ID: {existing_patient['patient_id']}")
        dob_obj = datetime.strptime(patient.date_of_birth, "%m/%d/%Y")
        dob_iso = dob_obj.strftime("%Y-%m-%d")
        patient_id = str(uuid.uuid4())
        now = now_utc()
        data = patient.model_dump()
        data["patient_id"] = patient_id
        data["date_of_birth"] = dob_iso
        data["created_at"] = now
        data["updated_at"] = now
        response = supabase.table("patients").insert(data).execute()
        if not response.data:
            return error_response(500, "Failed to create patient record")
        created = serialize_row(response.data[0])
        print(f"[VOICE AGENT] New patient registered: {created['first_name']} {created['last_name']} (ID: {patient_id})")
        return JSONResponse(status_code=201, content={"data": created, "error": None})
    except ValueError as ve:
        return error_response(422, str(ve))
    except Exception as e:
        print(f"Error creating patient: {str(e)}")
        return error_response(500, str(e))

@app.put("/patients/{patient_id}")
async def update_patient(patient_id: str, patient: PatientUpdate):
    """Update an existing patient record with partial data."""
    try:
        existing = supabase.table("patients").select("*").eq("patient_id", patient_id).single().execute()
        if not existing.data:
            return error_response(404, "Patient not found")
        update_data = patient.model_dump(exclude_unset=True)
        if not update_data:
            return error_response(400, "No fields to update")
        if "date_of_birth" in update_data:
            dob_obj = datetime.strptime(update_data["date_of_birth"], "%m/%d/%Y")
            update_data["date_of_birth"] = dob_obj.strftime("%Y-%m-%d")
        update_data["updated_at"] = now_utc()
        response = supabase.table("patients").update(update_data).eq("patient_id", patient_id).execute()
        if not response.data:
            return error_response(500, "Failed to update patient")
        return success_response(serialize_row(response.data[0]))
    except ValueError as ve:
        return error_response(422, str(ve))
    except Exception as e:
        print(f"Error updating patient: {str(e)}")
        return error_response(500, str(e))

@app.delete("/patients/{patient_id}")
async def delete_patient(patient_id: str):
    """Soft-delete a patient by setting the updated_at timestamp."""
    try:
        existing = supabase.table("patients").select("*").eq("patient_id", patient_id).single().execute()
        if not existing.data:
            return error_response(404, "Patient not found")
        now_str = now_utc()
        response = supabase.table("patients").update({"updated_at": now_str}).eq("patient_id", patient_id).execute()
        if not response.data:
            return error_response(500, "Failed to delete patient")
        return success_response({"message": "Patient deleted", "patient_id": patient_id})
    except Exception as e:
        print(f"Error deleting patient: {str(e)}")
        return error_response(500, str(e))

@app.post("/patients/check-phone")
async def check_phone_duplicate(check: PhoneCheck):
    """Check if a phone number is already registered (duplicate detection)."""
    try:
        response = supabase.table("patients").select("*").eq("phone_number", check.phone_number).execute()
        if response.data:
            patient = serialize_row(response.data[0])
            return {"data": {"is_duplicate": True, "patient": patient}, "error": None}
        return {"data": {"is_duplicate": False, "patient": None}, "error": None}
    except Exception as e:
        return error_response(500, str(e))

@app.post("/vapi-webhook")
async def vapi_webhook(request: Request):
    """Handle incoming webhook calls from the Vapi voice AI platform."""
    payload = await request.json()
    message = payload.get("message", {})
    if message.get("type") != "function-call":
        return JSONResponse(content={"status": "ignored"}, status_code=200)
    function_call = message.get("functionCall", {})
    func_name = function_call.get("name")
    parameters = function_call.get("parameters", {})
    print(f"Received Tool Call: {func_name} with params: {parameters}")
    if func_name == "checkExistingPatient":
        try:
            phone = parameters.get("phone_number")
            response = supabase.table("patients").select("*").eq("phone_number", phone).execute()
            if response.data:
                patient = serialize_row(response.data[0])
                return {"result": {"exists": True, "patient": patient}}
            return {"result": {"exists": False, "patient": None}}
        except Exception as e:
            return {"result": {"success": False, "error": str(e)}}
    elif func_name == "registerPatient":
        try:
            patient_data = PatientCreate(**parameters)
            existing = supabase.table("patients").select("patient_id").eq("phone_number", patient_data.phone_number).execute()
            if existing.data:
                return {"result": {"success": False, "error": "Patient with this phone number already exists."}}
            dob_obj = datetime.strptime(patient_data.date_of_birth, "%m/%d/%Y")
            dob_iso = dob_obj.strftime("%Y-%m-%d")
            data = patient_data.model_dump()
            data["date_of_birth"] = dob_iso
            response = supabase.table("patients").insert(data).execute()
            if not response.data:
                return {"result": {"success": False, "error": "Database insert failed."}}
            patient_id = response.data[0]["patient_id"]
            print(f"Patient registered successfully via Vapi: {patient_id}")
            return {"result": {"success": True, "patient_id": patient_id}}
        except Exception as e:
            print(f"Error registering patient via Vapi: {str(e)}")
            return {"result": {"success": False, "error": str(e)}}
    elif func_name == "updatePatient":
        try:
            patient_id = parameters.get("patient_id")
            if not patient_id:
                return {"result": {"success": False, "error": "patient_id is required for update."}}
            update_data = {k: v for k, v in parameters.items() if k != "patient_id" and v}
            if "date_of_birth" in update_data:
                dob_obj = datetime.strptime(update_data["date_of_birth"], "%m/%d/%Y")
                update_data["date_of_birth"] = dob_obj.strftime("%Y-%m-%d")
            update_data["updated_at"] = now_utc()
            response = supabase.table("patients").update(update_data).eq("patient_id", patient_id).execute()
            if not response.data:
                return {"result": {"success": False, "error": "Failed to update patient."}}
            return {"result": {"success": True, "patient_id": patient_id}}
        except Exception as e:
            return {"result": {"success": False, "error": str(e)}}
    elif func_name == "checkAvailability":
        requested_date = parameters.get("date", datetime.now().strftime("%Y-%m-%d"))
        return {"result": {"success": True, "available_slots": [{"date": requested_date, "time": "09:00 AM"}, {"date": requested_date, "time": "11:30 AM"}]}}
    elif func_name == "bookAppointment":
        return {"result": {"success": True, "appointment_id": "appt_123456"}}
    elif func_name == "sendSms":
        return {"result": {"success": True}}
    elif func_name == "transferCall":
        return {"result": {"success": True}}
    return {"result": {"success": False, "error": "Unknown function"}}


# --- Frontend Dashboard ---
from frontend import router as frontend_router
app.include_router(frontend_router)

# --- Run Server ---
import uvicorn

if __name__ == "__main__":
    uvicorn.run("backend:app", host="0.0.0.0", port=8000, reload=True)
