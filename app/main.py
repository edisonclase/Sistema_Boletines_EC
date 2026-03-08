from fastapi import FastAPI
from app.api.routes.students import router as students_router
from app.api.routes.data_sources import router as data_sources_router

app = FastAPI(
    title="Sistema_Boletines_EC",
    version="0.1.0",
    description="Sistema modular para boletines, consulta académica y estadísticas."
)

app.include_router(students_router)
app.include_router(data_sources_router)


@app.get("/")
def root():
    return {
        "message": "Sistema_Boletines_EC activo"
    }