from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from datetime import datetime
from app.models.patient import PatientCreate
from app.services.supabase import supabase
from app.utils.helpers import now_utc, serialize_row

router = APIRouter()


@router.post("/vapi-webhook")
async def vapi_webhook(request: Request):
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