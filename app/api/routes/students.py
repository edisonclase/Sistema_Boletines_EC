from fastapi import APIRouter
from app.services.bulletin_service import find_student_by_id

router = APIRouter(prefix="/students", tags=["students"])


@router.get("/{student_id}")
def get_student(student_id: str):
    return find_student_by_id(student_id)