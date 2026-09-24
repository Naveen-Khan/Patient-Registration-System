from supabase import create_client, Client
from datetime import datetime, timezone
from typing import Optional
from fastapi.responses import JSONResponse
from .config import SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY

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
