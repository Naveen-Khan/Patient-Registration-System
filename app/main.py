from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from app.routes.patient import router as patient_router
from app.routes.webhook import router as webhook_router
from app.routes.dashboard import router as dashboard_router
from app.utils.helpers import now_utc, error_response

app = FastAPI(title="Voice AI Agent - Patient Registration API")


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = [f"{'.'.join(str(x) for x in err['loc'])}: {err['msg']}" for err in exc.errors()]
    return JSONResponse(status_code=422, content={"data": None, "error": "; ".join(errors)})


@app.get("/")
def health_check():
    return {"data": {"message": "Voice AI Agent Backend is running!"}, "error": None}


app.include_router(patient_router)
app.include_router(webhook_router)
app.include_router(dashboard_router)


import uvicorn
if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)