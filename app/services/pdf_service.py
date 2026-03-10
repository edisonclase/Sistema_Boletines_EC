from __future__ import annotations

import re
import unicodedata
import zipfile
from io import BytesIO
from pathlib import Path

from pypdf import PdfReader, PdfWriter

from app.core.settings import settings
from app.data.fetchers.google_sheets import load_primer_ciclo, load_segundo_ciclo
from app.services.bulletin_service import find_student_by_id, normalize_student_id
from app.services.html_service import render_template
from app.utils.helpers import safe_value


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


def _normalize_text(value: str) -> str:
    value = safe_value(value)
    value = re.sub(r"\s+", " ", value).strip()
    return value.casefold()


def _normalize_cycle_name(value: str) -> str:
    text = _normalize_text(value)

    if text in {"primer_ciclo", "primer ciclo"}:
        return "Primer_Ciclo"

    if text in {"segundo_ciclo", "segundo ciclo"}:
        return "Segundo_Ciclo"

    return safe_value(value)


def _build_pdf_filename(result: dict) -> str:
    student = result.get("student", {})

    nombre = _sanitize_filename(student.get("nombre_estudiante", "Estudiante"))
    student_id = _sanitize_filename(student.get("id_estudiante", "sin_id"))
    curso = _sanitize_filename(student.get("curso", "sin_curso"))
    school_year = _sanitize_filename(settings.school_year)

    return f"{nombre} - {student_id} - {curso} - {school_year}.pdf"


def _build_blocks_pdf_filename(result: dict) -> str:
    student = result.get("student", {})

    nombre = _sanitize_filename(student.get("nombre_estudiante", "Estudiante"))
    student_id = _sanitize_filename(student.get("id_estudiante", "sin_id"))
    curso = _sanitize_filename(student.get("curso", "sin_curso"))
    school_year = _sanitize_filename(settings.school_year)

    return f"{nombre} - {student_id} - {curso} - {school_year} - bloques.pdf"


def _build_course_zip_filename(course: str, cycle: str, bulletin_type: str) -> str:
    safe_course = _sanitize_filename(course)
    safe_cycle = _sanitize_filename(cycle)
    safe_school_year = _sanitize_filename(settings.school_year)

    if bulletin_type == "blocks":
        return f"{safe_course} - {safe_cycle} - {safe_school_year} - boletines_bloques.zip"

    return f"{safe_course} - {safe_cycle} - {safe_school_year} - boletines_completos.zip"


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


def _build_blocks_bulletin_html(result: dict) -> str:
    if result["cycle"] != "Primer_Ciclo":
        raise ValueError("El boletín por bloques solo está disponible para Primer Ciclo.")

    html = render_template(
        "first_cycle_blocks.html",
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


def _load_cycle_dataframe(cycle: str):
    cycle = _normalize_cycle_name(cycle)

    if cycle == "Primer_Ciclo":
        df = load_primer_ciclo().copy()
    elif cycle == "Segundo_Ciclo":
        df = load_segundo_ciclo().copy()
    else:
        raise ValueError("El ciclo debe ser 'Primer_Ciclo' o 'Segundo_Ciclo'.")

    if "ID_ESTUDIANTE" in df.columns:
        df["ID_ESTUDIANTE"] = df["ID_ESTUDIANTE"].apply(normalize_student_id)

    if "CURSO" in df.columns:
        df["CURSO"] = df["CURSO"].apply(safe_value)

    return df, cycle


def _unique_filename(filename: str, used_names: set[str]) -> str:
    if filename not in used_names:
        used_names.add(filename)
        return filename

    stem, suffix = filename.rsplit(".", 1)
    counter = 2

    while True:
        candidate = f"{stem} ({counter}).{suffix}"
        if candidate not in used_names:
            used_names.add(candidate)
            return candidate
        counter += 1


def generate_complete_bulletin_pdf(student_id: str) -> tuple[bytes, str]:
    result = find_student_by_id(student_id)

    if not result.get("found"):
        raise ValueError(result.get("message", f"No se encontró el estudiante {student_id}"))

    html = _build_bulletin_html(result)
    bulletin_pdf_bytes = _generate_bulletin_pdf_bytes(html)
    final_pdf_bytes = _append_philosophy_pdf(bulletin_pdf_bytes)
    filename = _build_pdf_filename(result)

    return final_pdf_bytes, filename


def generate_blocks_bulletin_pdf(student_id: str) -> tuple[bytes, str]:
    result = find_student_by_id(student_id)

    if not result.get("found"):
        raise ValueError(result.get("message", f"No se encontró el estudiante {student_id}"))

    if result["cycle"] != "Primer_Ciclo":
        raise ValueError("El boletín por bloques solo está disponible para estudiantes de Primer Ciclo.")

    html = _build_blocks_bulletin_html(result)
    bulletin_pdf_bytes = _generate_bulletin_pdf_bytes(html)
    final_pdf_bytes = _append_philosophy_pdf(bulletin_pdf_bytes)
    filename = _build_blocks_pdf_filename(result)

    return final_pdf_bytes, filename


def generate_course_bulletins_zip(course: str, cycle: str, bulletin_type: str = "complete") -> tuple[bytes, str]:
    course = safe_value(course)

    if not course:
        raise ValueError("Debes indicar el curso.")

    if bulletin_type not in {"complete", "blocks"}:
        raise ValueError("El tipo de boletín debe ser 'complete' o 'blocks'.")

    df, normalized_cycle = _load_cycle_dataframe(cycle)

    if bulletin_type == "blocks" and normalized_cycle != "Primer_Ciclo":
        raise ValueError("El boletín por bloques masivo solo está disponible para Primer Ciclo.")

    if "CURSO" not in df.columns:
        raise ValueError("No existe la columna CURSO en la fuente de datos.")

    requested_course_normalized = _normalize_text(course)
    course_students = df[df["CURSO"].apply(_normalize_text) == requested_course_normalized]

    if course_students.empty:
        available_courses = sorted(
            {
                safe_value(value)
                for value in df["CURSO"].dropna().tolist()
                if safe_value(value)
            }
        )
        available_preview = ", ".join(available_courses[:12]) if available_courses else "sin cursos disponibles"
        raise ValueError(
            f"No se encontraron estudiantes para el curso '{course}' en {normalized_cycle}. "
            f"Cursos detectados: {available_preview}"
        )

    zip_buffer = BytesIO()
    used_names: set[str] = set()

    with zipfile.ZipFile(zip_buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as zip_file:
        for _, row in course_students.iterrows():
            student_id = normalize_student_id(row.get("ID_ESTUDIANTE"))

            if not student_id:
                continue

            if bulletin_type == "blocks":
                pdf_bytes, filename = generate_blocks_bulletin_pdf(student_id)
            else:
                pdf_bytes, filename = generate_complete_bulletin_pdf(student_id)

            final_name = _unique_filename(filename, used_names)
            zip_file.writestr(final_name, pdf_bytes)

    zip_buffer.seek(0)
    zip_filename = _build_course_zip_filename(course, normalized_cycle, bulletin_type)

    return zip_buffer.getvalue(), zip_filename


def generate_course_complete_bulletins_zip(course: str, cycle: str) -> tuple[bytes, str]:
    return generate_course_bulletins_zip(course=course, cycle=cycle, bulletin_type="complete")


def generate_course_blocks_bulletins_zip(course: str) -> tuple[bytes, str]:
    return generate_course_bulletins_zip(course=course, cycle="Primer_Ciclo", bulletin_type="blocks")