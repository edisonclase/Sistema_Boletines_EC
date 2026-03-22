from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.routes.audit import router as audit_router
from app.api.routes.auth import router as auth_router
from app.api.routes.data_sources import router as data_sources_router
from app.api.routes.students import router as students_router
from app.api.routes.ui import router as ui_router
from app.models import AuditLog, Role, SystemSetting, User  # noqa: F401
from modules.academic_tracking.routes import academic_tracking_bp



app = FastAPI(
    title="Sistema_Boletines_EC",
    version="0.1.0",
    description="Sistema modular para boletines, consulta académica y estadísticas."
)

app.mount("/assets", StaticFiles(directory="app/pdf/assets"), name="assets")

app.include_router(ui_router)
app.include_router(auth_router)
app.include_router(students_router)
app.include_router(data_sources_router)
app.include_router(audit_router)
app.register_blueprint(academic_tracking_bp)


@app.get("/health")
def health():
    return {
        "message": "Sistema_Boletines_EC activo"
    }