from app.routes.patient import router as patient_router
from app.routes.webhook import router as webhook_router
from app.routes.dashboard import router as dashboard_router

__all__ = ["patient_router", "webhook_router", "dashboard_router"]