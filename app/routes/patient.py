from fastapi import APIRouter, Query, Path
from typing import Optional
from app.services.supabase import supabase
from app.utils.helpers import now_utc, error_response, success_response, serialize_row
from app.models.patient import PatientCreate, PatientUpdate, PhoneCheck
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from datetime import datetime
import uuid

router = APIRouter()


@router.get("/patients")
async def list_patients(
    last_name: Optional[str] = Query(None, description="Filter patients by last name"),
    date_of_birth: Optional[str] = Query(None, description="Filter patients by date of birth (MM/DD/YYYY)"),
    phone_number: Optional[str] = Query(None, description="Filter patients by phone number"),
):
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


@router.get("/patients/{patient_id}")
async def get_patient(patient_id: str = Path(..., pattern=r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", description="Patient UUID")):
    try:
        response = supabase.table("patients").select("*").eq("patient_id", patient_id).single().execute()
        if not response.data:
            return error_response(404, "Patient not found")
        return success_response(serialize_row(response.data))
    except Exception as e:
        print(f"Error fetching patient: {str(e)}")
        return error_response(500, str(e))


@router.post("/patients", status_code=201)
async def create_patient(patient: PatientCreate):
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


@router.put("/patients/{patient_id}")
async def update_patient(patient_id: str, patient: PatientUpdate):
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


@router.delete("/patients/{patient_id}")
async def delete_patient(patient_id: str):
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


@router.post("/patients/check-phone")
async def check_phone_duplicate(check: PhoneCheck):
    try:
        response = supabase.table("patients").select("*").eq("phone_number", check.phone_number).execute()
        if response.data:
            patient = serialize_row(response.data[0])
            return {"data": {"is_duplicate": True, "patient": patient}, "error": None}
        return {"data": {"is_duplicate": False, "patient": None}, "error": None}
    except Exception as e:
        return error_response(500, str(e))