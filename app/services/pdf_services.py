from __future__ import annotations

import re
import unicodedata
from io import BytesIO
from pathlib import Path

from pypdf import PdfReader, PdfWriter
from weasyprint import HTML

from app.core.settings import settings
from app.services.bulletin_service import get_student_bulletin_data
from app.services.html_service import render_bulletin_html


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _resolve_path(path_str: str) -> Path:
    path = Path(path_str)
    if path.is_absolute():
        return path
    return _project_root() / path


def _sanitize_filename(value: str) -> str:
    """
    Limpia caracteres inválidos para nombres de archivos en Windows.
    """
    if not value:
        return "sin_valor"

    value = str(value).strip()
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    value = re.sub(r'[<>:"/\\|?*]', "", value)
    value = re.sub(r"\s+", " ", value).strip()
    return value or "sin_valor"


def build_pdf_filename(bulletin_data: dict) -> str:
    """
    Construye el nombre final del PDF:
    Nombre Completo - ID - Curso - Año Escolar.pdf
    """
    student = bulletin_data.get("student", {})

    nombre = (
        student.get("nombre_estudiante")
        or student.get("nombre")
        or "Estudiante"
    )
    student_id = (
        student.get("id_estudiante")
        or student.get("id")
        or "sin_id"
    )
    curso = student.get("curso") or "sin_curso"
    school_year = bulletin_data.get("school_year") or "sin_ano_escolar"

    nombre = _sanitize_filename(nombre)
    student_id = _sanitize_filename(student_id)
    curso = _sanitize_filename(curso)
    school_year = _sanitize_filename(school_year)

    return f"{nombre} - {student_id} - {curso} - {school_year}.pdf"


def generate_bulletin_pdf_bytes(student_id: str) -> tuple[bytes, dict]:
    """
    Genera el PDF base del boletín académico usando WeasyPrint
    y devuelve también la data del boletín.
    """
    bulletin_data = get_student_bulletin_data(student_id)
    html_content = render_bulletin_html(bulletin_data)

    pdf_bytes = HTML(
        string=html_content,
        base_url=str(_project_root())
    ).write_pdf()

    return pdf_bytes, bulletin_data


def append_philosophy_pdf(bulletin_pdf_bytes: bytes) -> bytes:
    """
    Une el boletín generado con el PDF de filosofía institucional.
    """
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
    """
    Genera el PDF final y el nombre correcto del archivo.
    """
    bulletin_pdf, bulletin_data = generate_bulletin_pdf_bytes(student_id)
    final_pdf = append_philosophy_pdf(bulletin_pdf)
    filename = build_pdf_filename(bulletin_data)

    return final_pdf, filename