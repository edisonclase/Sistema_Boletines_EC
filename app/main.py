from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.routes.audit import router as audit_router
from app.api.routes.auth import router as auth_router
from app.api.routes.data_sources import router as data_sources_router
from app.api.routes.students import router as students_router
from app.api.routes.ui import router as ui_router
from app.models import AuditLog, Role, SystemSetting, User  # noqa: F401
from academic_tracking.routes import router as academic_tracking_router


app = FastAPI(
    title="Sistema de Gestión Escolar Privado",
    version="0.1.0",
    description="Sistema de gestión escolar."
)

app.mount("/assets", StaticFiles(directory="app/pdf/assets"), name="assets")
app.mount("/static", StaticFiles(directory="academic_tracking/static"), name="static")

app.include_router(ui_router)
app.include_router(auth_router)
app.include_router(students_router)
app.include_router(data_sources_router)
app.include_router(audit_router)
app.include_router(academic_tracking_router)


@app.get("/health")
def health():
    return {
        "message": "El sistema de gestión escolar está operando correctamente."
    }