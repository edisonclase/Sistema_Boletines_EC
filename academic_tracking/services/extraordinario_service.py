"""
extraordinario_service.py

Servicio definitivo para construir datos de evaluación extraordinaria.

Reglas:
- Asignaturas académicas: *_CCF < 70 => Extraordinario.
- La asistencia NO se toma en cuenta para extraordinario.
- Los módulos formativos NO van a extraordinario.
- Solo se incluyen estudiantes con ESTADO = ACTIVO / ACTIVA.
"""

from __future__ import annotations

import math
import unicodedata
from typing import Any, Optional


ACADEMIC_SUBJECTS_PRIMER_CICLO = {
    "LEN": "Lengua Española",
    "ING": "Inglés",
    "FRA": "Francés",
    "MAT": "Matemática",
    "SOC": "Ciencias Sociales",
    "NAT": "Ciencias de la Naturaleza",
    "ART": "Educación Artística",
    "FIS": "Educación Física",
    "FOR": "Formación Humana",
}

ACADEMIC_SUBJECTS_SEGUNDO_CICLO = {
    "LEN": "Lengua Española",
    "ING": "Inglés",
    "MAT": "Matemática",
    "SOC": "Ciencias Sociales",
    "NAT": "Ciencias de la Naturaleza",
    "ART": "Educación Artística",
    "FIS": "Educación Física",
    "FOR": "Formación Humana",
}


def _normalize_text(value: Any) -> str:
    if value is None:
        return ""

    text = str(value).strip()

    if text.lower() == "nan":
        return ""

    if text.endswith(".0"):
        number_part = text[:-2]

        if number_part.isdigit():
            return number_part

    return text


def _normalize_key(value: Any) -> str:
    text = _normalize_text(value).upper()
    text = unicodedata.normalize("NFD", text)
    text = "".join(char for char in text if unicodedata.category(char) != "Mn")
    return text.strip()


def _has_sheet_error(value: Any) -> bool:
    text = _normalize_key(value)

    if not text:
        return False

    return text in {
        "#REF!",
        "#N/A",
        "#VALUE!",
        "#ERROR!",
        "#DIV/0!",
        "#NAME?",
        "#NUM!",
        "#NULL!",
    }


def _safe_float(value: Any) -> Optional[float]:
    if value is None:
        return None

    text = str(value).strip()

    if not text or text.lower() == "nan":
        return None

    text = text.replace("%", "").strip()

    if "/" in text:
        text = text.split("/", 1)[0].strip()

    try:
        number = float(text)
    except ValueError:
        return None

    if math.isnan(number):
        return None

    return number


def _format_score(value: Any) -> str:
    number = _safe_float(value)

    if number is None:
        return "—"

    return str(int(round(number)))


def _format_numero(value: Any) -> str:
    number = _safe_float(value)

    if number is not None:
        return str(int(number))

    text = _normalize_text(value)
    return text or "—"


def _is_active_row(row: dict[str, Any]) -> bool:
    status = _normalize_key(row.get("ESTADO"))

    if not status:
        return False

    return status in {"ACTIVO", "ACTIVA"}


def _split_course_name(course_name: Any) -> tuple[str, str]:
    text = _normalize_text(course_name)

    if not text:
        return "", ""

    parts = text.split(maxsplit=1)

    if len(parts) == 2:
        return parts[0].strip(), parts[1].strip()

    return text, ""


def _detect_cycle(row: dict[str, Any], ciclo: Optional[str] = None) -> str:
    if ciclo:
        return ciclo

    course_name = _normalize_text(row.get("CURSO"))
    course_key = _normalize_key(course_name)

    primer_ciclo_markers = {
        "1RO",
        "1ERO",
        "PRIMERO",
        "2DO",
        "SEGUNDO",
        "3RO",
        "TERCERO",
    }

    segundo_ciclo_markers = {
        "4TO",
        "CUARTO",
        "5TO",
        "QUINTO",
        "6TO",
        "SEXTO",
    }

    first_word = course_key.split(maxsplit=1)[0] if course_key else ""

    if first_word in primer_ciclo_markers:
        return "Primer Ciclo"

    if first_word in segundo_ciclo_markers:
        return "Segundo Ciclo"

    for module_number in range(1, 6):
        module_name = _normalize_text(row.get(f"MOD{module_number}_NOMBRE"))
        module_cf = _safe_float(row.get(f"MOD{module_number}_CF"))

        if module_name or module_cf is not None:
            return "Segundo Ciclo"

    return "Primer Ciclo"


def _subject_catalog_for_cycle(cycle: str) -> dict[str, str]:
    if _normalize_key(cycle) == "SEGUNDO CICLO":
        return ACADEMIC_SUBJECTS_SEGUNDO_CICLO

    return ACADEMIC_SUBJECTS_PRIMER_CICLO


def _matches_filters(
    *,
    course_name: str,
    grade: str,
    section: str,
    item_code: str,
    item_name: str,
    curso: Optional[str],
    grado: Optional[str],
    seccion: Optional[str],
    asignatura: Optional[str],
) -> bool:
    normalized_course = _normalize_text(curso)
    normalized_grade = _normalize_text(grado)
    normalized_section = _normalize_text(seccion)
    normalized_subject = _normalize_key(asignatura)

    if normalized_course and course_name != normalized_course:
        return False

    if normalized_grade and grade != normalized_grade:
        return False

    if normalized_section and section != normalized_section:
        return False

    if normalized_subject:
        if normalized_subject not in {_normalize_key(item_code), _normalize_key(item_name)}:
            return False

    return True


def build_extraordinario_report(
    *,
    rows: list[dict[str, Any]],
    ciclo: Optional[str] = None,
    curso: Optional[str] = None,
    grado: Optional[str] = None,
    seccion: Optional[str] = None,
    asignatura: Optional[str] = None,
    min_score: float = 70.0,
) -> dict[str, Any]:
    report_rows: list[dict[str, Any]] = []

    for row in rows or []:
        if not isinstance(row, dict):
            continue

        if not _is_active_row(row):
            continue

        detected_cycle = _detect_cycle(row, ciclo=ciclo)
        course_name = _normalize_text(row.get("CURSO"))
        raw_grade, raw_section = _split_course_name(course_name)

        student_id = _normalize_text(row.get("ID_ESTUDIANTE"))
        student_name = _normalize_text(row.get("NOMBRE_ESTUDIANTE"))

        if not student_id or not student_name:
            continue

        if _has_sheet_error(student_id) or _has_sheet_error(student_name):
            continue

        numero = _format_numero(row.get("NUMERO"))
        prof_titular = _normalize_text(row.get("PROF_TITULAR"))

        subject_catalog = _subject_catalog_for_cycle(detected_cycle)

        for subject_code, subject_name in subject_catalog.items():
            ccf_value = row.get(f"{subject_code}_CCF")

            if _has_sheet_error(ccf_value):
                continue

            ccf_score = _safe_float(ccf_value)

            if ccf_score is None:
                continue

            needs_extraordinario = ccf_score < min_score

            if not needs_extraordinario:
                continue

            if not _matches_filters(
                course_name=course_name,
                grade=raw_grade,
                section=raw_section,
                item_code=subject_code,
                item_name=subject_name,
                curso=curso,
                grado=grado,
                seccion=seccion,
                asignatura=asignatura,
            ):
                continue

            report_rows.append(
                {
                    "numero": numero,
                    "student_id": student_id,
                    "student_name": student_name,
                    "sexo": _normalize_text(row.get("SEXO")),
                    "estado": _normalize_text(row.get("ESTADO")),
                    "course_name": course_name,
                    "grade": raw_grade,
                    "section": raw_section,
                    "prof_titular": prof_titular,
                    "cycle": detected_cycle,
                    "item_code": subject_code,
                    "item_name": subject_name,
                    "item_type": "subject",
                    "ccf": _format_score(ccf_score),
                    "ccf_raw": ccf_score,
                    "reason": "No alcanzó la calificación mínima en completivo",
                    "reason_key": "extraordinario",
                }
            )

    report_rows = sorted(
        report_rows,
        key=lambda item: (
            _normalize_text(item.get("course_name")),
            _normalize_text(item.get("item_name")),
            _normalize_text(item.get("numero")).zfill(4),
            _normalize_text(item.get("student_name")),
        ),
    )

    grouped_courses = _group_rows_by_course_and_item(report_rows)
    students = _group_rows_by_student(report_rows)

    return {
        "summary": {
            "total_cases": len(report_rows),
            "total_students": len(students),
            "subjects_cases": len(report_rows),
            "modules_cases": 0,
        },
        "rows": report_rows,
        "students": students,
        "grouped_courses": grouped_courses,
    }


def _group_rows_by_course_and_item(
    report_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    grouped_by_course: dict[str, dict[str, Any]] = {}

    for item in report_rows:
        course_name = _normalize_text(item.get("course_name")) or "Sin curso"
        item_name = _normalize_text(item.get("item_name")) or "Sin asignatura"

        grouped_by_course.setdefault(
            course_name,
            {
                "course_name": course_name,
                "subjects": {},
            },
        )

        grouped_by_course[course_name]["subjects"].setdefault(
            item_name,
            {
                "subject_name": item_name,
                "students": [],
            },
        )

        grouped_by_course[course_name]["subjects"][item_name]["students"].append(item)

    grouped_courses = []

    for course_payload in grouped_by_course.values():
        grouped_courses.append(
            {
                "course_name": course_payload["course_name"],
                "subjects": sorted(
                    course_payload["subjects"].values(),
                    key=lambda item: _normalize_text(item.get("subject_name")),
                ),
            }
        )

    return sorted(
        grouped_courses,
        key=lambda item: _normalize_text(item.get("course_name")),
    )


def _group_rows_by_student(
    report_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], dict[str, Any]] = {}

    for item in report_rows:
        key = (
            _normalize_text(item.get("student_id")),
            _normalize_text(item.get("course_name")),
        )

        if key not in grouped:
            grouped[key] = {
                "numero": item.get("numero"),
                "student_id": item.get("student_id"),
                "student_name": item.get("student_name"),
                "sexo": item.get("sexo"),
                "estado": item.get("estado"),
                "course_name": item.get("course_name"),
                "grade": item.get("grade"),
                "section": item.get("section"),
                "prof_titular": item.get("prof_titular"),
                "cycle": item.get("cycle"),
                "items": [],
                "reason": "Evaluación extraordinaria",
                "reason_key": "extraordinario",
            }

        grouped[key]["items"].append(item)

    students = list(grouped.values())

    return sorted(
        students,
        key=lambda item: (
            _normalize_text(item.get("course_name")),
            _normalize_text(item.get("numero")).zfill(4),
            _normalize_text(item.get("student_name")),
        ),
    )