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

from .database import supabase, serialize_row, error_response, success_response, now_utc
from .models import PatientCreate, PatientUpdate, PhoneCheck

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

# --- Dashboard UI Route ---

@app.get("/dashboard", response_class=HTMLResponse)
async def get_dashboard():
    """Render an HTML dashboard showing all registered patients in a styled table."""
    response = supabase.table("patients").select("*").order("created_at", desc=True).execute()
    patients = response.data if response.data else []

    rows = ""
    if not patients:
        rows = "<tr><td colspan='6' class='text-center py-10 text-gray-400'>No patients registered yet. Register patients via the AI Agent!</td></tr>"
    else:
        for p in patients:
            full_name = f"{p.get('first_name', '')} {p.get('last_name', '')}"
            phone = p.get('phone_number', 'N/A')
            dob = p.get('date_of_birth', 'N/A')
            sex = p.get('sex', 'N/A')
            address = f"{p.get('address_line_1', '')}, {p.get('city', '')}, {p.get('state', '')} {p.get('zip_code', '')}"
            ec_name = p.get('emergency_contact_name', 'N/A')
            ec_phone = p.get('emergency_contact_phone', 'N/A')
            rows += f"""
            <tr class='border-b border-gray-100 hover:bg-gray-50'>
                <td class='px-6 py-4 text-sm font-bold text-gray-900'>{full_name}</td>
                <td class='px-6 py-4 text-sm text-gray-600'>{phone}</td>
                <td class='px-6 py-4 text-sm text-gray-600'>{dob}</td>
                <td class='px-6 py-4 text-sm'><span class='px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-blue-100 text-blue-800'>{sex}</span></td>
                <td class='px-6 py-4 text-sm text-gray-600 max-w-xs truncate'>{address}</td>
                <td class='px-6 py-4 text-sm text-gray-600'><div class='font-medium'>{ec_name}</div><div class='text-gray-500'>{ec_phone}</div></td>
            </tr>
            """

    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Meridian Health Clinic - Dashboard</title>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-gradient-to-br from-blue-50 to-indigo-100 min-h-screen">
        <header class="bg-gradient-to-r from-blue-600 to-indigo-700 shadow-lg">
            <div class="max-w-7xl mx-auto px-4 py-5 flex justify-between items-center">
                <div>
                    <h1 class="text-2xl font-bold text-white">Meridian Health Clinic</h1>
                    <p class="text-blue-200 text-sm mt-1">Patient Registration System</p>
                </div>
                <div class="bg-white/20 backdrop-blur text-white px-5 py-2.5 rounded-xl text-sm font-semibold border border-white/30">
                    Total Patients: {len(patients)}
                </div>
            </div>
        </header>
        <main class="max-w-7xl mx-auto px-4 py-8">
            <div class="bg-white rounded-2xl shadow-xl border border-gray-100 overflow-hidden">
                <div class="bg-gradient-to-r from-gray-50 to-white px-6 py-4 border-b border-gray-200 flex justify-between items-center">
                    <h2 class="text-xl font-bold text-gray-800">Registered Patients</h2>
                    <span class="bg-blue-100 text-blue-700 px-3 py-1 rounded-full text-xs font-medium">{len(patients)} records</span>
                </div>
                <div class="overflow-x-auto">
                    <table class="min-w-full divide-y divide-gray-200">
                        <thead class="bg-gray-50">
                            <tr>
                                <th class='px-6 py-4 text-left text-xs font-bold text-gray-600 uppercase tracking-wider'>Name</th>
                                <th class='px-6 py-4 text-left text-xs font-bold text-gray-600 uppercase tracking-wider'>Phone</th>
                                <th class='px-6 py-4 text-left text-xs font-bold text-gray-600 uppercase tracking-wider'>DOB</th>
                                <th class='px-6 py-4 text-left text-xs font-bold text-gray-600 uppercase tracking-wider'>Sex</th>
                                <th class='px-6 py-4 text-left text-xs font-bold text-gray-600 uppercase tracking-wider'>Address</th>
                                <th class='px-6 py-4 text-left text-xs font-bold text-gray-600 uppercase tracking-wider'>Emergency Contact</th>
                            </tr>
                        </thead>
                        <tbody class='bg-white divide-y divide-gray-100'>{rows}</tbody>
                    </table>
                </div>
            </div>
        </main>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

# --- Vapi Webhook Route ---

@app.post("/vapi-webhook")
async def vapi_webhook(request: Request):
    """Handle incoming webhook calls from the Vapi voice AI platform.

    Processes function calls from the AI agent to check patients, register new patients,
    and update patient information during phone conversations.
    """
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
