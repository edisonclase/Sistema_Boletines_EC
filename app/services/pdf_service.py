from __future__ import annotations

import re
import unicodedata
import zipfile
from io import BytesIO
from pathlib import Path

from pypdf import PdfReader, PdfWriter

from app.core.settings import settings
from app.data.fetchers.google_sheets import load_primer_ciclo, load_segundo_ciclo
from app.services.bulletin_service import (
    build_student_result_from_row,
    find_student_by_id,
    normalize_student_id,
)
from app.services.html_service import (
    render_second_cycle_blocks_and_modules,
    render_second_cycle_modules_only,
    render_template,
)
from app.utils.helpers import safe_value


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _resolve_path(path_str: str) -> Path:
    path = Path(path_str)
    if path.is_absolute():
        return path
    return _project_root() / path


def _load_css_text(css_filename: str) -> str:
    css_path = _project_root() / "app" / "pdf" / "templates" / "css" / css_filename

    if not css_path.exists():
        print(f"[PDF] No se encontró el CSS: {css_path}", flush=True)
        return ""

    return css_path.read_text(encoding="utf-8")


def _sanitize_filename(value: str) -> str:
    if not value:
        return "sin_valor"

    value = str(value).strip()
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    value = re.sub(r'[<>:"/\\\\|?*]', "", value)
    value = re.sub(r"\s+", " ", value).strip()

    return value or "sin_valor"


def _normalize_text(value: str) -> str:
    value = safe_value(value)
    value = re.sub(r"\s+", " ", value).strip()
    return value.casefold()


def _normalize_course_name(value: str) -> str:
    text = safe_value(value).strip().casefold()
    text = text.replace("º", "o").replace("°", "o")
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"\b(\d+)\s*(?:do|to|ro|mo|vo|no|er|o)\b", r"\1", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _normalize_cycle_name(value: str) -> str:
    text = _normalize_text(value)

    if text in {"primer_ciclo", "primer ciclo"}:
        return "Primer_Ciclo"

    if text in {"segundo_ciclo", "segundo ciclo"}:
        return "Segundo_Ciclo"

    return safe_value(value)


def _truncate_name(value: str, max_len: int = 48) -> str:
    value = _sanitize_filename(value)
    return value[:max_len].strip() if len(value) > max_len else value


def _normalize_ascii_text(value: str) -> str:
    value = safe_value(value).strip()
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    value = re.sub(r"\s+", " ", value).strip()
    return value


def _extract_course_level_token(course: str) -> str:
    normalized = _normalize_ascii_text(course)
    match = re.search(r"\b(\d+)\s*(do|to|ro|mo|vo|no|er|o)\b", normalized, flags=re.IGNORECASE)

    if match:
        return f"{match.group(1)}{match.group(2).lower()}"

    fallback = re.search(r"\b(\d+)\b", normalized)
    if fallback:
        return fallback.group(1)

    return ""


def _abbreviate_second_cycle_course(course: str) -> str:
    original = safe_value(course)
    if not original:
        return "Segundo_Ciclo"

    normalized = _normalize_ascii_text(original)
    level_token = _extract_course_level_token(normalized)

    text_without_level = normalized

    if level_token:
        text_without_level = re.sub(
            r"^\s*" + re.escape(level_token) + r"\b",
            "",
            text_without_level,
            flags=re.IGNORECASE,
        ).strip()

    words = re.findall(r"[A-Za-z0-9]+", text_without_level)

    stopwords = {
        "y", "de", "del", "la", "las", "el", "los", "en", "para", "con", "e",
        "da", "do", "al"
    }

    significant_words = [w for w in words if w.casefold() not in stopwords]

    if not significant_words:
        abbreviated_body = _sanitize_filename(normalized.replace(" ", "_"))
        return abbreviated_body or "Segundo_Ciclo"

    if len(significant_words) == 1:
        abbreviated_body = significant_words[0][:4].upper()
    else:
        abbreviated_body = "".join(word[0].upper() for word in significant_words)

    if level_token:
        return f"{level_token}_{abbreviated_body}"

    return abbreviated_body


def _build_zip_course_label(course: str, cycle: str) -> str:
    safe_course = _sanitize_filename(course)

    if cycle == "Segundo_Ciclo":
        abbreviated = _abbreviate_second_cycle_course(course)
        return _sanitize_filename(abbreviated)

    return safe_course


def _build_pdf_filename(result: dict) -> str:
    student = result.get("student", {})
    nombre = _truncate_name(student.get("nombre_estudiante", "Estudiante"))
    student_id = _sanitize_filename(student.get("id_estudiante", "sin_id"))

    return f"{student_id} - {nombre}.pdf"


def _build_blocks_pdf_filename(result: dict) -> str:
    student = result.get("student", {})
    nombre = _truncate_name(student.get("nombre_estudiante", "Estudiante"))
    student_id = _sanitize_filename(student.get("id_estudiante", "sin_id"))

    return f"{student_id} - {nombre} - bloques.pdf"


def _build_modules_only_pdf_filename(result: dict) -> str:
    student = result.get("student", {})
    nombre = _truncate_name(student.get("nombre_estudiante", "Estudiante"))
    student_id = _sanitize_filename(student.get("id_estudiante", "sin_id"))

    return f"{student_id} - {nombre} - modulos.pdf"


def _build_blocks_and_modules_pdf_filename(result: dict) -> str:
    student = result.get("student", {})
    nombre = _truncate_name(student.get("nombre_estudiante", "Estudiante"))
    student_id = _sanitize_filename(student.get("id_estudiante", "sin_id"))

    return f"{student_id} - {nombre} - bloques_modulos.pdf"


def _build_course_zip_filename(course: str, cycle: str, bulletin_type: str) -> str:
    safe_course = _build_zip_course_label(course, cycle)
    safe_cycle = _sanitize_filename(cycle)

    if bulletin_type == "blocks":
        return f"{safe_cycle} - {safe_course} - bloques.zip"

    if bulletin_type == "modules_only":
        return f"{safe_cycle} - {safe_course} - modulos.zip"

    if bulletin_type == "blocks_and_modules":
        return f"{safe_cycle} - {safe_course} - bloques_modulos.zip"

    return f"{safe_cycle} - {safe_course} - completos.zip"


def _build_bulletin_html(result: dict) -> str:

    if result["cycle"] == "Primer_Ciclo":
        template_name = "first_cycle_bulletin.html"
        specific_css = _load_css_text("first_cycle_bulletin.css")

    else:
        template_name = "second_cycle_bulletin.html"
        specific_css = _load_css_text("second_cycle_bulletin.css")

    return render_template(
        template_name,
        {
            "institution_name": settings.institution_name,
            "student": result["student"],
            "cycle": result["cycle"],
            "logo_path": settings.institution_logo,
            "school_year": settings.school_year,
            "bulletin_specific_css": specific_css,
        }
    )


def _build_blocks_bulletin_html(result: dict) -> str:

    if result["cycle"] != "Primer_Ciclo":
        raise ValueError("El boletín por bloques solo está disponible para Primer Ciclo.")

    return render_template(
        "first_cycle_blocks.html",
        {
            "institution_name": settings.institution_name,
            "student": result["student"],
            "cycle": result["cycle"],
            "logo_path": settings.institution_logo,
            "school_year": settings.school_year,
        }
    )


def _build_modules_only_bulletin_html(result: dict) -> str:

    if result["cycle"] != "Segundo_Ciclo":
        raise ValueError("El boletín solo de módulos solo está disponible para Segundo Ciclo.")

    return render_second_cycle_modules_only(
        result["student"],
        {
            "institution_name": settings.institution_name,
            "cycle": result["cycle"],
            "logo_path": settings.institution_logo,
            "school_year": settings.school_year,
        }
    )


def _build_blocks_and_modules_bulletin_html(result: dict) -> str:

    if result["cycle"] != "Segundo_Ciclo":
        raise ValueError("El boletín por bloques y módulos solo está disponible para Segundo Ciclo.")

    return render_second_cycle_blocks_and_modules(
        result["student"],
        {
            "institution_name": settings.institution_name,
            "cycle": result["cycle"],
            "logo_path": settings.institution_logo,
            "school_year": settings.school_year,
        }
    )


def _generate_bulletin_pdf_bytes(html: str) -> bytes:
    from weasyprint import HTML

    return HTML(
        string=html,
        base_url=str(_project_root())
    ).write_pdf()


def _get_philosophy_pdf_path() -> Path:
    philosophy_path = _resolve_path(settings.philosophy_pdf_path)

    if not philosophy_path.exists():
        raise FileNotFoundError(
            f"No se encontró el PDF de filosofía en: {philosophy_path}"
        )

    return philosophy_path


def _append_philosophy_pdf(bulletin_pdf_bytes: bytes) -> bytes:

    philosophy_path = _get_philosophy_pdf_path()

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


def _should_append_philosophy(bulletin_type: str) -> bool:
    if bulletin_type == "complete":
        return False
    return True


def _generate_final_pdf_from_result(
    result: dict,
    bulletin_type: str,
    append_philosophy: bool | None = None
) -> tuple[bytes, str]:

    if append_philosophy is None:
        append_philosophy = _should_append_philosophy(bulletin_type)

    if bulletin_type == "blocks":

        if result["cycle"] != "Primer_Ciclo":
            raise ValueError("El boletín por bloques solo está disponible para estudiantes de Primer Ciclo.")

        html = _build_blocks_bulletin_html(result)
        filename = _build_blocks_pdf_filename(result)

    elif bulletin_type == "modules_only":

        if result["cycle"] != "Segundo_Ciclo":
            raise ValueError("El boletín solo de módulos solo está disponible para estudiantes de Segundo Ciclo.")

        html = _build_modules_only_bulletin_html(result)
        filename = _build_modules_only_pdf_filename(result)

    elif bulletin_type == "blocks_and_modules":

        if result["cycle"] != "Segundo_Ciclo":
            raise ValueError("El boletín por bloques y módulos solo está disponible para estudiantes de Segundo Ciclo.")

        html = _build_blocks_and_modules_bulletin_html(result)
        filename = _build_blocks_and_modules_pdf_filename(result)

    else:

        html = _build_bulletin_html(result)
        filename = _build_pdf_filename(result)

    bulletin_pdf_bytes = _generate_bulletin_pdf_bytes(html)

    if append_philosophy:
        final_pdf_bytes = _append_philosophy_pdf(bulletin_pdf_bytes)
    else:
        final_pdf_bytes = bulletin_pdf_bytes

    return final_pdf_bytes, filename


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

    return _generate_final_pdf_from_result(result, "complete", append_philosophy=False)


def generate_blocks_bulletin_pdf(student_id: str) -> tuple[bytes, str]:

    result = find_student_by_id(student_id)

    if not result.get("found"):
        raise ValueError(result.get("message", f"No se encontró el estudiante {student_id}"))

    return _generate_final_pdf_from_result(result, "blocks", append_philosophy=True)


def generate_modules_only_bulletin_pdf(student_id: str) -> tuple[bytes, str]:

    result = find_student_by_id(student_id)

    if not result.get("found"):
        raise ValueError(result.get("message", f"No se encontró el estudiante {student_id}"))

    if result.get("cycle") != "Segundo_Ciclo":
        raise ValueError("El boletín solo de módulos solo está disponible para estudiantes de Segundo Ciclo.")

    return _generate_final_pdf_from_result(result, "modules_only", append_philosophy=True)


def generate_blocks_and_modules_bulletin_pdf(student_id: str) -> tuple[bytes, str]:

    result = find_student_by_id(student_id)

    if not result.get("found"):
        raise ValueError(result.get("message", f"No se encontró el estudiante {student_id}"))

    if result.get("cycle") != "Segundo_Ciclo":
        raise ValueError("El boletín por bloques y módulos solo está disponible para estudiantes de Segundo Ciclo.")

    return _generate_final_pdf_from_result(result, "blocks_and_modules", append_philosophy=True)


def generate_course_bulletins_zip(course: str, cycle: str, bulletin_type: str = "complete") -> tuple[bytes, str]:

    course = safe_value(course)

    if not course:
        raise ValueError("Debes indicar el curso.")

    if bulletin_type not in {"complete", "blocks", "modules_only", "blocks_and_modules"}:
        raise ValueError("El tipo de boletín debe ser 'complete', 'blocks', 'modules_only' o 'blocks_and_modules'.")

    df, normalized_cycle = _load_cycle_dataframe(cycle)

    if bulletin_type == "blocks" and normalized_cycle != "Primer_Ciclo":
        raise ValueError("El boletín por bloques masivo solo está disponible para Primer Ciclo.")

    if bulletin_type in {"modules_only", "blocks_and_modules"} and normalized_cycle != "Segundo_Ciclo":
        raise ValueError("Este tipo de boletín masivo solo está disponible para Segundo Ciclo.")

    if "CURSO" not in df.columns:
        raise ValueError("No existe la columna CURSO en la fuente de datos.")

    requested_course_normalized = _normalize_course_name(course)

    course_students = df[df["CURSO"].apply(_normalize_course_name) == requested_course_normalized]

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

    total_students = len(course_students)

    print(
        f"[ZIP] Iniciando generación masiva | curso={course} | ciclo={normalized_cycle} | "
        f"tipo={bulletin_type} | estudiantes={total_students}",
        flush=True
    )

    zip_buffer = BytesIO()

    used_names: set[str] = set()

    append_philosophy = _should_append_philosophy(bulletin_type)

    with zipfile.ZipFile(zip_buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as zip_file:

        for index, (_, row) in enumerate(course_students.iterrows(), start=1):

            result = build_student_result_from_row(row, normalized_cycle)

            student_name = safe_value(result["student"].get("nombre_estudiante"))
            student_id = safe_value(result["student"].get("id_estudiante"))

            print(
                f"[ZIP] Generando {index}/{total_students} | {student_name} | ID={student_id}",
                flush=True
            )

            pdf_bytes, filename = _generate_final_pdf_from_result(
                result,
                bulletin_type,
                append_philosophy=append_philosophy
            )

            final_name = _unique_filename(filename, used_names)

            zip_file.writestr(final_name, pdf_bytes)

    zip_buffer.seek(0)

    zip_filename = _build_course_zip_filename(course, normalized_cycle, bulletin_type)

    print(f"[ZIP] ZIP completado: {zip_filename}", flush=True)

    return zip_buffer.getvalue(), zip_filename


def generate_course_complete_bulletins_zip(course: str, cycle: str) -> tuple[bytes, str]:
    return generate_course_bulletins_zip(course=course, cycle=cycle, bulletin_type="complete")


def generate_course_blocks_bulletins_zip(course: str) -> tuple[bytes, str]:
    return generate_course_bulletins_zip(course=course, cycle="Primer_Ciclo", bulletin_type="blocks")


def generate_course_modules_only_bulletins_zip(course: str) -> tuple[bytes, str]:
    return generate_course_bulletins_zip(course=course, cycle="Segundo_Ciclo", bulletin_type="modules_only")


def generate_course_blocks_and_modules_bulletins_zip(course: str) -> tuple[bytes, str]:
    return generate_course_bulletins_zip(course=course, cycle="Segundo_Ciclo", bulletin_type="blocks_and_modules")