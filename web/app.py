import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "api", ".env"))

from flask import Flask, render_template, request, redirect, url_for, flash
from supabase import create_client

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "patient-registration-secret-key-change-me")

supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_ROLE_KEY"))

US_STATES = ["AL","AK","AZ","AR","CA","CO","CT","DE","FL","GA","HI","ID","IL","IN","IA","KS","KY","LA","ME","MD","MA","MI","MN","MS","MO","MT","NE","NV","NH","NJ","NM","NY","NC","ND","OH","OK","OR","PA","RI","SC","SD","TN","TX","UT","VT","VA","WA","WV","WI","WY"]


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/patients")
def patients():
    response = supabase.table("patients").select("*").order("created_at", desc=True).execute()
    patients = response.data if response.data else []
    return render_template("patients.html", patients=patients)


@app.route("/patients", methods=["POST"])
def add_patient():
    data = {
        "patient_id": __import__("uuid").uuid4().hex,
        "first_name": request.form.get("first_name"),
        "last_name": request.form.get("last_name"),
        "date_of_birth": request.form.get("date_of_birth"),
        "sex": request.form.get("sex"),
        "phone_number": request.form.get("phone_number"),
        "address_line_1": request.form.get("address_line_1"),
        "city": request.form.get("city"),
        "state": request.form.get("state"),
        "zip_code": request.form.get("zip_code"),
        "email": request.form.get("email") or None,
        "address_line_2": request.form.get("address_line_2") or None,
        "insurance_provider": request.form.get("insurance_provider") or None,
        "insurance_member_id": request.form.get("insurance_member_id") or None,
        "preferred_language": request.form.get("preferred_language", "English"),
        "emergency_contact_name": request.form.get("emergency_contact_name") or None,
        "emergency_contact_phone": request.form.get("emergency_contact_phone") or None,
        "created_at": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
        "updated_at": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
    }
    response = supabase.table("patients").insert(data).execute()
    if response.data:
        flash("Patient registered successfully!", "success")
    else:
        flash("Error registering patient.", "error")
    return redirect(url_for("patients"))


@app.route("/patients/<patient_id>/delete", methods=["POST"])
def delete_patient(patient_id):
    now = __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat()
    supabase.table("patients").update({"updated_at": now}).eq("patient_id", patient_id).execute()
    flash("Patient deleted.", "success")
    return redirect(url_for("patients"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)