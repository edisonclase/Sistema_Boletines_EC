from fastapi import APIRouter

router = APIRouter(prefix="/students", tags=["students"])


@router.get("/{student_id}")
def get_student(student_id: str):
    return {
        "student_id": student_id,
        "message": "Ruta base de estudiante lista"
    }