import os
from datetime import datetime, timezone
from typing import Optional
import uuid, re

from fastapi import FastAPI, Request, Query, Path
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, HTMLResponse
from pydantic import BaseModel, Field, field_validator, ConfigDict
from supabase import create_client

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env.local"), override=False)

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    raise RuntimeError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set. Add them to Vercel project settings or .env.local.")

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

app = FastAPI(title="Voice AI Agent - Patient Registration API")

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = [f"{'.'.join(str(x) for x in err['loc'])}: {err['msg']}" for err in exc.errors()]
    return JSONResponse(status_code=422, content={"data": None, "error": "; ".join(errors)})

def now_utc() -> str: return datetime.now(timezone.utc).isoformat()
def error_response(status_code: int, detail: str) -> JSONResponse: return JSONResponse(status_code=status_code, content={"data": None, "error": detail})
def success_response(data: dict) -> JSONResponse: return JSONResponse(status_code=200, content={"data": data, "error": None})
def serialize_row(row: Optional[dict]) -> Optional[dict]:
    if not row: return None
    row.pop("deleted_at", None)
    return row

US_STATE_ABBR = {"AL","AK","AZ","AR","CA","CO","CT","DE","FL","GA","HI","ID","IL","IN","IA","KS","KY","LA","ME","MD","MA","MI","MN","MS","MO","MT","NE","NV","NH","NJ","NM","NY","NC","ND","OH","OK","OR","PA","RI","SC","SD","TN","TX","UT","VT","VA","WA","WV","WI","WY"}

class PatientCreate(BaseModel):
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
        if not re.match(r"^[A-Za-z\-']{1,50}$", v): raise ValueError("Name must be 1-50 chars, alphabetic with hyphens/apostrophes only")
        return v

    @field_validator("state")
    @classmethod
    def validate_state(cls, v: str) -> str:
        if v not in US_STATE_ABBR: raise ValueError("State must be a valid 2-letter US state abbreviation")
        return v

    @field_validator("zip_code")
    @classmethod
    def validate_zip(cls, v: str) -> str:
        if not re.match(r"^\d{5}(-\d{4})?$", v): raise ValueError("ZIP code must be 5-digit or ZIP+4 format")
        return v

    @field_validator("phone_number")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        if len(re.sub(r"[^\d]", "", v)) != 10: raise ValueError("Phone must be a valid 10-digit US phone number")
        return v

    @field_validator("emergency_contact_phone")
    @classmethod
    def validate_emergency_phone(cls, v: Optional[str]) -> Optional[str]:
        if v and len(re.sub(r"[^\d]", "", v)) != 10: raise ValueError("Emergency contact phone must be a valid 10-digit US phone number")
        return v

    @field_validator("date_of_birth")
    @classmethod
    def validate_dob(cls, v: str) -> str:
        try:
            dob = datetime.strptime(v, "%m/%d/%Y")
            if dob > datetime.now(): raise ValueError("Date of birth cannot be in the future")
        except ValueError: raise ValueError("Date of birth must be a valid date in MM/DD/YYYY format and not in the future")
        return v

class PatientUpdate(BaseModel):
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
        if v and not re.match(r"^[A-Za-z\-']{1,50}$", v): raise ValueError("Name must be 1-50 chars, alphabetic with hyphens/apostrophes only")
        return v

    @field_validator("state")
    @classmethod
    def validate_state(cls, v: Optional[str]) -> Optional[str]:
        if v and v not in US_STATE_ABBR: raise ValueError("State must be a valid 2-letter US state abbreviation")
        return v

    @field_validator("zip_code")
    @classmethod
    def validate_zip(cls, v: Optional[str]) -> Optional[str]:
        if v and not re.match(r"^\d{5}(-\d{4})?$", v): raise ValueError("ZIP code must be 5-digit or ZIP+4 format")
        return v

    @field_validator("phone_number")
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        if v and len(re.sub(r"[^\d]", "", v)) != 10: raise ValueError("Phone must be a valid 10-digit US phone number")
        return v

    @field_validator("emergency_contact_phone")
    @classmethod
    def validate_emergency_phone(cls, v: Optional[str]) -> Optional[str]:
        if v and len(re.sub(r"[^\d]", "", v)) != 10: raise ValueError("Emergency contact phone must be a valid 10-digit US phone number")
        return v

    @field_validator("date_of_birth")
    @classmethod
    def validate_dob(cls, v: Optional[str]) -> Optional[str]:
        if v:
            try:
                dob = datetime.strptime(v, "%m/%d/%Y")
                if dob > datetime.now(): raise ValueError("Date of birth cannot be in the future")
            except ValueError: raise ValueError("Date of birth must be a valid date in MM/DD/YYYY format and not in the future")
        return v

class PhoneCheck(BaseModel):
    phone_number: str

@app.get("/")
def health_check():
    return {"data": {"message": "Voice AI Agent Backend is running!"}, "error": None}

@app.get("/patients")
async def list_patients(last_name: Optional[str] = Query(None), date_of_birth: Optional[str] = Query(None), phone_number: Optional[str] = Query(None)):
    try:
        query = supabase.table("patients").select("*")
        if last_name: query = query.ilike("last_name", f"%{last_name}%")
        if date_of_birth: query = query.eq("date_of_birth", date_of_birth)
        if phone_number: query = query.eq("phone_number", phone_number)
        response = query.execute()
        if response.data is None: return error_response(500, "Failed to fetch patients")
        return {"data": [serialize_row(row) for row in response.data], "error": None}
    except Exception as e: return error_response(500, str(e))

@app.get("/patients/{patient_id}")
async def get_patient(patient_id: str = Path(..., pattern=r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")):
    try:
        response = supabase.table("patients").select("*").eq("patient_id", patient_id).single().execute()
        if not response.data: return error_response(404, "Patient not found")
        return success_response(serialize_row(response.data))
    except Exception as e: return error_response(500, str(e))

@app.post("/patients", status_code=201)
async def create_patient(patient: PatientCreate):
    try:
        existing = supabase.table("patients").select("patient_id").eq("phone_number", patient.phone_number).execute()
        if existing.data: return error_response(409, f"Patient already exists. ID: {serialize_row(existing.data[0])['patient_id']}")
        dob_iso = datetime.strptime(patient.date_of_birth, "%m/%d/%Y").strftime("%Y-%m-%d")
        patient_id = str(uuid.uuid4())
        now = now_utc()
        data = patient.model_dump()
        data.update({"patient_id": patient_id, "date_of_birth": dob_iso, "created_at": now, "updated_at": now})
        response = supabase.table("patients").insert(data).execute()
        if not response.data: return error_response(500, "Failed to create patient")
        created = serialize_row(response.data[0])
        print(f"[VOICE AGENT] New patient: {created['first_name']} {created['last_name']} (ID: {patient_id})")
        return JSONResponse(status_code=201, content={"data": created, "error": None})
    except ValueError as ve: return error_response(422, str(ve))
    except Exception as e: return error_response(500, str(e))

@app.put("/patients/{patient_id}")
async def update_patient(patient_id: str, patient: PatientUpdate):
    try:
        existing = supabase.table("patients").select("*").eq("patient_id", patient_id).single().execute()
        if not existing.data: return error_response(404, "Patient not found")
        update_data = patient.model_dump(exclude_unset=True)
        if not update_data: return error_response(400, "No fields to update")
        if "date_of_birth" in update_data:
            update_data["date_of_birth"] = datetime.strptime(update_data["date_of_birth"], "%m/%d/%Y").strftime("%Y-%m-%d")
        update_data["updated_at"] = now_utc()
        response = supabase.table("patients").update(update_data).eq("patient_id", patient_id).execute()
        if not response.data: return error_response(500, "Failed to update patient")
        return success_response(serialize_row(response.data[0]))
    except ValueError as ve: return error_response(422, str(ve))
    except Exception as e: return error_response(500, str(e))

@app.delete("/patients/{patient_id}")
async def delete_patient(patient_id: str):
    try:
        existing = supabase.table("patients").select("*").eq("patient_id", patient_id).single().execute()
        if not existing.data: return error_response(404, "Patient not found")
        response = supabase.table("patients").update({"updated_at": now_utc()}).eq("patient_id", patient_id).execute()
        if not response.data: return error_response(500, "Failed to delete patient")
        return success_response({"message": "Patient deleted", "patient_id": patient_id})
    except Exception as e: return error_response(500, str(e))

@app.post("/patients/check-phone")
async def check_phone_duplicate(check: PhoneCheck):
    try:
        response = supabase.table("patients").select("*").eq("phone_number", check.phone_number).execute()
        if response.data: return {"data": {"is_duplicate": True, "patient": serialize_row(response.data[0])}, "error": None}
        return {"data": {"is_duplicate": False, "patient": None}, "error": None}
    except Exception as e: return error_response(500, str(e))

@app.post("/vapi-webhook")
async def vapi_webhook(request: Request):
    payload = await request.json()
    message = payload.get("message", {})
    if message.get("type") != "function-call": return JSONResponse(content={"status": "ignored"}, status_code=200)
    function_call = message.get("functionCall", {})
    func_name = function_call.get("name")
    parameters = function_call.get("parameters", {})
    print(f"Received Tool Call: {func_name}")
    if func_name == "checkExistingPatient":
        try:
            response = supabase.table("patients").select("*").eq("phone_number", parameters.get("phone_number")).execute()
            if response.data: return {"result": {"exists": True, "patient": serialize_row(response.data[0])}}
            return {"result": {"exists": False, "patient": None}}
        except Exception as e: return {"result": {"success": False, "error": str(e)}}
    elif func_name == "registerPatient":
        try:
            patient_data = PatientCreate(**parameters)
            existing = supabase.table("patients").select("patient_id").eq("phone_number", patient_data.phone_number).execute()
            if existing.data: return {"result": {"success": False, "error": "Patient with this phone already exists."}}
            dob_iso = datetime.strptime(patient_data.date_of_birth, "%m/%d/%Y").strftime("%Y-%m-%d")
            data = patient_data.model_dump()
            data["date_of_birth"] = dob_iso
            response = supabase.table("patients").insert(data).execute()
            if not response.data: return {"result": {"success": False, "error": "Database insert failed."}}
            patient_id = response.data[0]["patient_id"]
            print(f"Patient registered via Vapi: {patient_id}")
            return {"result": {"success": True, "patient_id": patient_id}}
        except Exception as e:
            print(f"Error: {str(e)}")
            return {"result": {"success": False, "error": str(e)}}
    elif func_name == "updatePatient":
        try:
            patient_id = parameters.get("patient_id")
            if not patient_id: return {"result": {"success": False, "error": "patient_id is required."}}
            update_data = {k: v for k, v in parameters.items() if k != "patient_id" and v}
            if "date_of_birth" in update_data:
                update_data["date_of_birth"] = datetime.strptime(update_data["date_of_birth"], "%m/%d/%Y").strftime("%Y-%m-%d")
            update_data["updated_at"] = now_utc()
            response = supabase.table("patients").update(update_data).eq("patient_id", patient_id).execute()
            if not response.data: return {"result": {"success": False, "error": "Failed to update patient."}}
            return {"result": {"success": True, "patient_id": patient_id}}
        except Exception as e: return {"result": {"success": False, "error": str(e)}}
    elif func_name == "checkAvailability":
        return {"result": {"success": True, "available_slots": [{"date": parameters.get("date", datetime.now().strftime("%Y-%m-%d")), "time": "09:00 AM"}]}}
    elif func_name in ("bookAppointment", "sendSms", "transferCall"):
        return {"result": {"success": True, "appointment_id": "appt_123456" if func_name == "bookAppointment" else None}}
    return {"result": {"success": False, "error": "Unknown function"}}

@app.get("/dashboard", response_class=HTMLResponse)
async def get_dashboard():
    response = supabase.table("patients").select("*").order("created_at", desc=True).execute()
    patients = response.data if response.data else []
    rows = ""
    if not patients:
        rows = "<tr><td colspan='6' class='empty'>No patients registered.</td></tr>"
    else:
        for p in patients:
            full_name = f"{p.get('first_name', '')} {p.get('last_name', '')}"
            rows += f"<tr><td>{full_name}</td><td>{p.get('phone_number','N/A')}</td><td>{p.get('date_of_birth','N/A')}</td><td>{p.get('sex','N/A')}</td><td>{p.get('address_line_1','')}, {p.get('city','')}, {p.get('state','')}</td><td>{p.get('emergency_contact_name','N/A')}</td></tr>"
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Meridian Health Clinic - Patient Registration</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f0f4f8; color: #333; }}
  .container {{ max-width: 1100px; margin: 40px auto; padding: 0 20px; }}
  .header {{ background: linear-gradient(135deg, #1a73e8, #0d47a1); color: #fff; padding: 30px 40px; border-radius: 12px 12px 0 0; }}
  .header h1 {{ font-size: 28px; margin-bottom: 8px; }}
  .header p {{ opacity: 0.9; font-size: 16px; }}
  .stats {{ background: #fff; padding: 20px 40px; border-bottom: 1px solid #e0e0e0; }}
  .stats span {{ font-size: 20px; font-weight: 700; color: #1a73e8; }}
  table {{ width: 100%; border-collapse: collapse; background: #fff; border-radius: 0 0 12px 12px; overflow: hidden; box-shadow: 0 2px 12px rgba(0,0,0,0.08); }}
  th {{ background: #1a73e8; color: #fff; padding: 14px 16px; text-align: left; font-size: 14px; text-transform: uppercase; letter-spacing: 0.5px; }}
  td {{ padding: 12px 16px; border-bottom: 1px solid #eee; font-size: 14px; }}
  tr:hover {{ background: #f5f8fd; }}
  tr:last-child td {{ border-bottom: none; }}
  .empty {{ text-align: center; padding: 40px; color: #999; font-size: 16px; }}
  .nav {{ background: #fff; padding: 14px 40px; border-bottom: 1px solid #e0e0e0; }}
  .nav a {{ color: #1a73e8; text-decoration: none; font-size: 14px; margin-right: 20px; font-weight: 500; }}
  .nav a:hover {{ text-decoration: underline; }}
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <h1>Meridian Health Clinic</h1>
    <p>Patient Registration System</p>
  </div>
  <div class="nav">
    <a href="/">Home</a>
    <a href="/patients">View All Patients</a>
  </div>
  <div class="stats">
    <p>Total Patients: <span>{len(patients)}</span></p>
  </div>
  <table>
    <thead>
      <tr><th>Name</th><th>Phone</th><th>DOB</th><th>Sex</th><th>Address</th><th>Emergency Contact</th></tr>
    </thead>
    <tbody>
      {rows}
    </tbody>
  </table>
</div>
</body>
</html>"""
    return HTMLResponse(content=html)

import uvicorn
if __name__ == "__main__":
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)
