"""
completivo_service.py

Servicio definitivo para construir datos de completivo.

Reglas:
- Asignaturas académicas: CF_FINAL < 70 => Completivo.
- Módulos formativos: MODx_CF < 70 => Completivo.
- Asistencia: solo entra si la hoja auxiliar indica DECISION_GESTION = COMPLETIVO.
- DECISION_GESTION = PROMOVIDO no entra por asistencia.
"""

from __future__ import annotations

import math
import unicodedata
from typing import Any, Optional


INACTIVE_STATUS_WORDS = {
    "ABANDONO",
    "ABANDONO",
    "ABANDONO",
    "RETIRADO",
    "RETIRADA",
    "TRANSFERIDO",
    "TRANSFERIDA",
    "TRASLADADO",
    "TRASLADADA",
    "INACTIVO",
    "INACTIVA",
    "BAJA",
}

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


def _format_module_score(value: Any) -> str:
    number = _safe_float(value)

    if number is None:
        return "—"

    return f"{int(round(number))}/100"


def _format_percent(value: Any) -> str:
    number = _safe_float(value)

    if number is None:
        return "—"

    return f"{int(round(number))}%"


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


def _build_attendance_control_index(
    attendance_rows: list[dict[str, Any]],
) -> dict[tuple[str, str], dict[str, Any]]:
    index: dict[tuple[str, str], dict[str, Any]] = {}

    for row in attendance_rows or []:
        student_id = _normalize_text(row.get("ID_ESTUDIANTE"))
        course_name = _normalize_text(row.get("CURSO"))

        if not student_id:
            continue

        index[(student_id, course_name)] = row
        index[(student_id, "")] = row

    return index


def _get_attendance_control_row(
    index: dict[tuple[str, str], dict[str, Any]],
    student_id: str,
    course_name: str,
) -> Optional[dict[str, Any]]:
    return index.get((student_id, course_name)) or index.get((student_id, ""))


def _matches_filters(
    *,
    course_name: str,
    grade: str,
    section: str,
    item_code: str,
    item_name: str,
    motivo: Optional[str],
    reason_key: str,
    curso: Optional[str],
    grado: Optional[str],
    seccion: Optional[str],
    asignatura: Optional[str],
) -> bool:
    normalized_course = _normalize_text(curso)
    normalized_grade = _normalize_text(grado)
    normalized_section = _normalize_text(seccion)
    normalized_subject = _normalize_key(asignatura)
    normalized_motivo = _normalize_key(motivo)

    if normalized_course and course_name != normalized_course:
        return False

    if normalized_grade and grade != normalized_grade:
        return False

    if normalized_section and section != normalized_section:
        return False

    if normalized_subject:
        if normalized_subject not in {_normalize_key(item_code), _normalize_key(item_name)}:
            return False

    if normalized_motivo:
        if normalized_motivo != _normalize_key(reason_key):
            return False

    return True


def _resolve_reason_key(has_grade: bool, has_attendance: bool) -> str:
    if has_grade and has_attendance:
        return "ambas"

    if has_grade:
        return "calificacion"

    return "asistencia"


def _resolve_reason_label(reason_key: str) -> str:
    labels = {
        "calificacion": "Calificación final",
        "asistencia": "Asistencia",
        "ambas": "Calificación final y asistencia",
    }

    return labels.get(reason_key, reason_key)


def _attendance_level(value: Any) -> str:
    number = _safe_float(value)

    if number is None:
        return ""

    if number <= 75:
        return "critical"

    if number < 80:
        return "warning"

    return ""


def build_completivo_report(
    *,
    rows: list[dict[str, Any]],
    attendance_rows_primer_ciclo: Optional[list[dict[str, Any]]] = None,
    attendance_rows_segundo_ciclo: Optional[list[dict[str, Any]]] = None,
    ciclo: Optional[str] = None,
    curso: Optional[str] = None,
    grado: Optional[str] = None,
    seccion: Optional[str] = None,
    asignatura: Optional[str] = None,
    motivo: Optional[str] = None,
    min_score: float = 70.0,
) -> dict[str, Any]:
    primer_attendance_index = _build_attendance_control_index(
        attendance_rows_primer_ciclo or []
    )
    segundo_attendance_index = _build_attendance_control_index(
        attendance_rows_segundo_ciclo or []
    )

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

        attendance_index = (
            segundo_attendance_index
            if _normalize_key(detected_cycle) == "SEGUNDO CICLO"
            else primer_attendance_index
        )

        attendance_control_row = _get_attendance_control_row(
            attendance_index,
            student_id,
            course_name,
        )

        subject_catalog = _subject_catalog_for_cycle(detected_cycle)

        for subject_code, subject_name in subject_catalog.items():
            cf_final = _safe_float(row.get(f"{subject_code}_CF_FINAL"))

            needs_by_grade = cf_final is not None and cf_final < min_score

            attendance_value = None
            decision = ""

            if attendance_control_row:
                attendance_value = attendance_control_row.get(
                    f"{subject_code}_ASISTENCIA_ANUAL"
                )
                decision = _normalize_key(
                    attendance_control_row.get(f"{subject_code}_DECISION_GESTION")
                )

            needs_by_attendance = decision == "COMPLETIVO"

            if not needs_by_grade and not needs_by_attendance:
                continue

            reason_key = _resolve_reason_key(
                has_grade=needs_by_grade,
                has_attendance=needs_by_attendance,
            )

            if not _matches_filters(
                course_name=course_name,
                grade=raw_grade,
                section=raw_section,
                item_code=subject_code,
                item_name=subject_name,
                motivo=motivo,
                reason_key=reason_key,
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
                    "cf_final": _format_score(cf_final),
                    "cf_raw": cf_final,
                    "attendance_pct": _format_percent(attendance_value),
                    "attendance_raw": _safe_float(attendance_value),
                    "attendance_level": _attendance_level(attendance_value),
                    "attendance_decision": decision or "—",
                    "reason": _resolve_reason_label(reason_key),
                    "reason_key": reason_key,
                    "observation": (
                        _normalize_text(attendance_control_row.get("OBSERVACION"))
                        if attendance_control_row
                        else ""
                    ),
                }
            )

        if _normalize_key(detected_cycle) == "SEGUNDO CICLO":
            for module_number in range(1, 6):
                module_code = f"MOD{module_number}"
                module_name = _normalize_text(row.get(f"{module_code}_NOMBRE"))

                if not module_name:
                    module_name = f"Módulo formativo {module_number}"

                raw_module_cf = row.get(f"{module_code}_CF")

                if _has_sheet_error(raw_module_cf):
                    continue

                module_cf = _safe_float(raw_module_cf)

                if module_cf is None:
                    continue

                needs_by_grade = module_cf < min_score

                attendance_value = None
                decision = ""

                if attendance_control_row:
                    attendance_value = attendance_control_row.get(
                        f"{module_code}_ASISTENCIA_ANUAL"
                    )
                    decision = _normalize_key(
                        attendance_control_row.get(f"{module_code}_DECISION_GESTION")
                    )

                needs_by_attendance = decision == "COMPLETIVO"

                if not needs_by_grade and not needs_by_attendance:
                    continue

                reason_key = _resolve_reason_key(
                    has_grade=needs_by_grade,
                    has_attendance=needs_by_attendance,
                )

                if not _matches_filters(
                    course_name=course_name,
                    grade=raw_grade,
                    section=raw_section,
                    item_code=module_code,
                    item_name=module_name,
                    motivo=motivo,
                    reason_key=reason_key,
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
                        "item_code": module_code,
                        "item_name": module_name,
                        "item_type": "module",
                        "cf_final": _format_module_score(module_cf),
                        "cf_raw": module_cf,
                        "attendance_pct": _format_percent(attendance_value),
                        "attendance_raw": _safe_float(attendance_value),
                        "attendance_level": _attendance_level(attendance_value),
                        "attendance_decision": decision or "—",
                        "reason": _resolve_reason_label(reason_key),
                        "reason_key": reason_key,
                        "observation": (
                            _normalize_text(attendance_control_row.get("OBSERVACION"))
                            if attendance_control_row
                            else ""
                        ),
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
            "by_grade": sum(
                1 for item in report_rows if item.get("reason_key") == "calificacion"
            ),
            "by_attendance": sum(
                1 for item in report_rows if item.get("reason_key") == "asistencia"
            ),
            "by_both": sum(
                1 for item in report_rows if item.get("reason_key") == "ambas"
            ),
            "subjects_cases": sum(
                1 for item in report_rows if item.get("item_type") == "subject"
            ),
            "modules_cases": sum(
                1 for item in report_rows if item.get("item_type") == "module"
            ),
            "attendance_critical": sum(
                1 for item in report_rows if item.get("attendance_level") == "critical"
            ),
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
                "reasons": set(),
            }

        grouped[key]["items"].append(item)
        grouped[key]["reasons"].add(item.get("reason_key"))

    students = []

    for student in grouped.values():
        reasons = student.pop("reasons", set())

        if "ambas" in reasons or {"calificacion", "asistencia"}.issubset(reasons):
            general_reason = "Calificación final y asistencia"
            general_reason_key = "ambas"
        elif "calificacion" in reasons:
            general_reason = "Calificación final"
            general_reason_key = "calificacion"
        else:
            general_reason = "Asistencia"
            general_reason_key = "asistencia"

        student["reason"] = general_reason
        student["reason_key"] = general_reason_key
        students.append(student)

    return sorted(
        students,
        key=lambda item: (
            _normalize_text(item.get("course_name")),
            _normalize_text(item.get("numero")).zfill(4),
            _normalize_text(item.get("student_name")),
        ),
    )