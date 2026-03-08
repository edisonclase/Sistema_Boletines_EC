from __future__ import annotations

import re
import unicodedata
from io import BytesIO
from pathlib import Path

from pypdf import PdfReader, PdfWriter

from app.core.settings import settings
from app.services.bulletin_service import find_student_by_id
from app.services.html_service import render_template


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _resolve_path(path_str: str) -> Path:
    path = Path(path_str)
    if path.is_absolute():
        return path
    return _project_root() / path


def _sanitize_filename(value: str) -> str:
    if not value:
        return "sin_valor"

    value = str(value).strip()
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    value = re.sub(r'[<>:"/\\|?*]', "", value)
    value = re.sub(r"\s+", " ", value).strip()

    return value or "sin_valor"


def _build_pdf_filename(result: dict) -> str:
    student = result.get("student", {})

    nombre = _sanitize_filename(student.get("nombre_estudiante", "Estudiante"))
    student_id = _sanitize_filename(student.get("id_estudiante", "sin_id"))
    curso = _sanitize_filename(student.get("curso", "sin_curso"))
    school_year = _sanitize_filename(settings.school_year)

    return f"{nombre} - {student_id} - {curso} - {school_year}.pdf"


def _build_bulletin_html(result: dict) -> str:
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
            "school_year": settings.school_year,
        }
    )

    return html


def _generate_bulletin_pdf_bytes(html: str) -> bytes:
    from weasyprint import HTML

    pdf_bytes = HTML(
        string=html,
        base_url=str(_project_root())
    ).write_pdf()

    return pdf_bytes


def _append_philosophy_pdf(bulletin_pdf_bytes: bytes) -> bytes:
    philosophy_path = _resolve_path(settings.philosophy_pdf_path)

    if not philosophy_path.exists():
        raise FileNotFoundError(
            f"No se encontró el PDF de filosofía en: {philosophy_path}"
        )

    writer = PdfWriter()

    bulletin_reader = PdfReader(BytesIO(bulletin_pdf_bytes))
    for page in bulletin_reader.pages:
        writer.add_page(page)

    philosophy_reader = PdfReader(str(philosophy_path))
    for page in philosophy_reader.pages:
        writer.add_page(page)

    output = BytesIO()
    writer.write(output)
    output.seek(0)

    return output.getvalue()


def generate_complete_bulletin_pdf(student_id: str) -> tuple[bytes, str]:
    result = find_student_by_id(student_id)

    if not result.get("found"):
        raise ValueError(result.get("message", f"No se encontró el estudiante {student_id}"))

    html = _build_bulletin_html(result)
    bulletin_pdf_bytes = _generate_bulletin_pdf_bytes(html)
    final_pdf_bytes = _append_philosophy_pdf(bulletin_pdf_bytes)
    filename = _build_pdf_filename(result)

    return final_pdf_bytes, filename