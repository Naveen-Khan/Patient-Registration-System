from datetime import datetime, timezone
from typing import Optional
from fastapi.responses import JSONResponse


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def error_response(status_code: int, detail: str) -> JSONResponse:
    return JSONResponse(status_code=status_code, content={"data": None, "error": detail})


def success_response(data: dict) -> JSONResponse:
    return JSONResponse(status_code=200, content={"data": data, "error": None})


def serialize_row(row: Optional[dict]) -> Optional[dict]:
    if not row:
        return None
    row.pop("deleted_at", None)
    return row