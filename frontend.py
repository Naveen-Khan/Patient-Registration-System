"""Frontend Dashboard - HTML table for viewing registered patients."""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

router = APIRouter()

@router.get("/dashboard", response_class=HTMLResponse)
async def get_dashboard():
    from backend import supabase, serialize_row
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
