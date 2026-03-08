from datetime import datetime

from fastapi import APIRouter
from fastapi.responses import HTMLResponse, Response

from app.core.settings import settings
from app.services.bulletin_service import find_student_by_id
from app.services.html_service import render_template
from app.services.pdf_service import generate_complete_bulletin_pdf

router = APIRouter(prefix="/students", tags=["students"])


@router.get("/{student_id}")
def get_student(student_id: str):
    return find_student_by_id(student_id)


@router.get("/{student_id}/bulletin-html", response_class=HTMLResponse)
def get_student_bulletin_html(student_id: str):
    result = find_student_by_id(student_id)

    if not result.get("found"):
        return HTMLResponse(
            content=f"<h1>No se encontró ningún estudiante con el ID {student_id}</h1>",
            status_code=404
        )

    template_name = (
        "first_cycle_bulletin.html"
        if result["cycle"] == "Primer_Ciclo"
        else "second_cycle_bulletin.html"
    )

    html = render_template(
        template_name,
        {
            "institution_name": settings.institution_name,
            "student": result["student"],
            "cycle": result["cycle"],
            "logo_path": settings.institution_logo,
            "generated_at": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "generated_by": settings.bulletin_generated_by,
            "school_year": settings.school_year,
        }
    )

    return HTMLResponse(content=html)


@router.get("/{student_id}/bulletin-pdf")
def get_student_bulletin_pdf(student_id: str):
    result = find_student_by_id(student_id)

    if not result.get("found"):
        return HTMLResponse(
            content=f"<h1>No se encontró ningún estudiante con el ID {student_id}</h1>",
            status_code=404
        )

    pdf_bytes, filename = generate_complete_bulletin_pdf(student_id)

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
    )