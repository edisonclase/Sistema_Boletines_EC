"""
tracking_service.py

Servicio principal de construcción del dashboard del módulo academic_tracking.

Responsabilidades:
- Consumir filas crudas del origen de datos
- Aplicar parsing y evaluación de riesgo académico
- Construir métricas resumidas para el dashboard
- Organizar resultados por curso, período y asignatura
- Mantener el payload listo para render HTML o salida JSON
"""

from __future__ import annotations

from typing import Any, Optional

from .parsing_service import (
    get_detected_academic_subjects,
    get_supported_period_codes,
)
from .risk_service import (
    PERIOD_STATUS_COMPROMISED,
    PERIOD_STATUS_INCOMPLETE,
    PERIOD_STATUS_PASSED,
    build_risk_entries_from_rows,
)


DASHBOARD_STATUS_REFERENCE = {
    "reported": "reported",
    "partial": "partial",
    "pending": "pending",
}


def _normalize_filter_value(value: Optional[Any]) -> Optional[str]:
    """
    Normaliza filtros textuales.
    """
    if value is None:
        return None

    text = str(value).strip()
    if not text:
        return None

    return text


def _apply_entry_filters(
    entries: list[dict[str, Any]],
    course_name: Optional[str] = None,
    period_code: Optional[str] = None,
    subject_code: Optional[str] = None,
) -> list[dict[str, Any]]:
    """
    Filtra entradas ya evaluadas por curso, período y asignatura.
    """
    filtered = entries

    normalized_course = _normalize_filter_value(course_name)
    normalized_period = _normalize_filter_value(period_code)
    normalized_subject = _normalize_filter_value(subject_code)

    if normalized_course:
        filtered = [
            entry
            for entry in filtered
            if str(entry.get("curso", "")).strip() == normalized_course
        ]

    if normalized_period:
        filtered = [
            entry
            for entry in filtered
            if str(entry.get("period_code", "")).strip() == normalized_period
        ]

    if normalized_subject:
        filtered = [
            entry
            for entry in filtered
            if str(entry.get("subject_code", "")).strip() == normalized_subject
        ]

    return filtered


def _extract_detected_courses(entries: list[dict[str, Any]]) -> list[str]:
    """
    Detecta cursos presentes en las entradas.
    """
    return sorted(
        {
            str(entry.get("curso", "")).strip()
            for entry in entries
            if str(entry.get("curso", "")).strip()
        }
    )


def _count_summary_statuses(entries: list[dict[str, Any]]) -> dict[str, int]:
    """
    Cuenta cuántas entradas están reportadas, parciales o con período comprometido.
    """
    reported = sum(
        1 for entry in entries if entry.get("period_status") == PERIOD_STATUS_PASSED
    )
    partial = sum(
        1 for entry in entries if entry.get("period_status") == PERIOD_STATUS_INCOMPLETE
    )
    pending = sum(
        1
        for entry in entries
        if entry.get("period_status") == PERIOD_STATUS_COMPROMISED
    )

    return {
        "reported": reported,
        "partial": partial,
        "pending": pending,
    }


def _build_unique_students_at_risk(
    entries: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Construye una lista única de estudiantes con períodos comprometidos.
    Agrupa por estudiante + curso.
    """
    grouped: dict[tuple[str, str], dict[str, Any]] = {}

    for entry in entries:
        if entry.get("period_status") != PERIOD_STATUS_COMPROMISED:
            continue

        student_id = entry.get("student_id", "")
        course_name = entry.get("curso", "")
        key = (student_id, course_name)

        if key not in grouped:
            grouped[key] = {
                "student": {
                    "id_estudiante": student_id,
                    "nombre_estudiante": entry.get("student_name", ""),
                    "numero": entry.get("numero", ""),
                    "curso": course_name,
                },
                "subjects_at_risk_count": 0,
                "failed_blocks_count": 0,
                "entries": [],
            }

        grouped[key]["subjects_at_risk_count"] += 1
        grouped[key]["failed_blocks_count"] += int(entry.get("failed_blocks_count", 0))
        grouped[key]["entries"].append(entry)

    return sorted(
        grouped.values(),
        key=lambda item: (
            item["student"].get("curso", ""),
            item["student"].get("numero", ""),
            item["student"].get("nombre_estudiante", ""),
        ),
    )


def _build_period_cards(entries: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
    """
    Construye resumen por período para tarjetas superiores.
    """
    period_codes = get_supported_period_codes()
    cards: dict[str, dict[str, int]] = {}

    for period_code in period_codes:
        period_entries = [
            entry for entry in entries if entry.get("period_code") == period_code
        ]

        cards[period_code] = {
            "reported_subjects": sum(
                1
                for entry in period_entries
                if entry.get("period_status") == PERIOD_STATUS_PASSED
            ),
            "partial_subjects": sum(
                1
                for entry in period_entries
                if entry.get("period_status") == PERIOD_STATUS_INCOMPLETE
            ),
            "pending_subjects": sum(
                1
                for entry in period_entries
                if entry.get("period_status") == PERIOD_STATUS_COMPROMISED
            ),
            "students_at_risk_count": len(
                {
                    (entry.get("student_id", ""), entry.get("curso", ""))
                    for entry in period_entries
                    if entry.get("period_status") == PERIOD_STATUS_COMPROMISED
                }
            ),
            "failed_competencies_count": sum(
                int(entry.get("failed_blocks_count", 0)) for entry in period_entries
            ),
        }

    return cards


def _map_entry_to_subject_row(entry: dict[str, Any]) -> dict[str, Any]:
    """
    Convierte una entrada evaluada a una fila de resumen por asignatura/período.
    """
    status = entry.get("period_status")

    if status == PERIOD_STATUS_PASSED:
        dashboard_status = DASHBOARD_STATUS_REFERENCE["reported"]
        status_label = "Reportado"

    elif status == PERIOD_STATUS_INCOMPLETE:
        dashboard_status = DASHBOARD_STATUS_REFERENCE["partial"]
        status_label = "Parcial"

    else:
        dashboard_status = DASHBOARD_STATUS_REFERENCE["pending"]
        status_label = "Período comprometido"

    reported_blocks_count = int(entry.get("reported_blocks_count", 0))
    coverage_pct = round((reported_blocks_count / 4) * 100, 2)

    return {
        "subject_code": entry.get("subject_code", ""),
        "subject_name": entry.get("subject_name", ""),
        "status": dashboard_status,
        "status_label": status_label,
        "coverage_pct": coverage_pct,
        "students_with_any_report": 1 if reported_blocks_count > 0 else 0,
        "students_without_report": 1 if reported_blocks_count == 0 else 0,
        "students_at_risk_count": 1 if status == PERIOD_STATUS_COMPROMISED else 0,
        "failed_competencies_count": int(entry.get("failed_blocks_count", 0)),
        "docente_asignatura": "",
        "failed_blocks": entry.get("failed_blocks", []),
        "student_id": entry.get("student_id", ""),
        "student_name": entry.get("student_name", ""),
        "numero": entry.get("numero", ""),
    }


def _group_course_period_subjects(
    entries: list[dict[str, Any]],
    teacher_assignments: Optional[list[dict[str, Any]]] = None,
) -> list[dict[str, Any]]:
    """
    Organiza la vista detallada por curso -> período -> asignatura.

    Nota:
    - teacher_assignments queda preparado para futura integración real.
    - Por ahora, si no hay asignación docente, se deja vacío.
    """
    teacher_lookup: dict[tuple[str, str], str] = {}

    if teacher_assignments:
        for item in teacher_assignments:
            course_name = str(item.get("course_name", "")).strip()
            subject_code = str(item.get("subject_code", "")).strip()
            teacher_name = str(item.get("teacher_name", "")).strip()

            if course_name and subject_code and teacher_name:
                teacher_lookup[(course_name, subject_code)] = teacher_name

    courses_map: dict[str, dict[str, Any]] = {}

    for entry in entries:
        course_name = str(entry.get("curso", "")).strip()
        period_code = str(entry.get("period_code", "")).strip()
        subject_code = str(entry.get("subject_code", "")).strip()

        if not course_name or not period_code or not subject_code:
            continue

        if course_name not in courses_map:
            courses_map[course_name] = {
                "curso": course_name,
                "total_students": len(
                    {
                        e.get("student_id", "")
                        for e in entries
                        if str(e.get("curso", "")).strip() == course_name
                    }
                ),
                "periods": {},
            }

        if period_code not in courses_map[course_name]["periods"]:
            courses_map[course_name]["periods"][period_code] = {
                "totals": {
                    "reported": 0,
                    "partial": 0,
                    "pending": 0,
                },
                "students_at_risk_count": 0,
                "subjects": [],
                "students_at_risk": [],
            }

        period_bucket = courses_map[course_name]["periods"][period_code]
        subject_row = _map_entry_to_subject_row(entry)
        subject_row["docente_asignatura"] = teacher_lookup.get(
            (course_name, subject_code), ""
        )

        period_bucket["subjects"].append(subject_row)

        if subject_row["status"] == DASHBOARD_STATUS_REFERENCE["reported"]:
            period_bucket["totals"]["reported"] += 1
        elif subject_row["status"] == DASHBOARD_STATUS_REFERENCE["partial"]:
            period_bucket["totals"]["partial"] += 1
        else:
            period_bucket["totals"]["pending"] += 1

    for course_name, course_payload in courses_map.items():
        for period_code in get_supported_period_codes():
            if period_code not in course_payload["periods"]:
                continue

            period_entries = [
                entry
                for entry in entries
                if str(entry.get("curso", "")).strip() == course_name
                and str(entry.get("period_code", "")).strip() == period_code
                and entry.get("period_status") == PERIOD_STATUS_COMPROMISED
            ]

            grouped_students: dict[str, dict[str, Any]] = {}

            for entry in period_entries:
                student_id = entry.get("student_id", "")
                if student_id not in grouped_students:
                    grouped_students[student_id] = {
                        "student": {
                            "id_estudiante": student_id,
                            "nombre_estudiante": entry.get("student_name", ""),
                            "numero": entry.get("numero", ""),
                            "curso": course_name,
                        },
                        "subjects_at_risk_count": 0,
                        "failed_competencies_count": 0,
                        "details": [],
                    }

                grouped_students[student_id]["subjects_at_risk_count"] += 1
                grouped_students[student_id]["failed_competencies_count"] += int(
                    entry.get("failed_blocks_count", 0)
                )
                grouped_students[student_id]["details"].append(
                    {
                        "subject_code": entry.get("subject_code", ""),
                        "subject_name": entry.get("subject_name", ""),
                        "failed_blocks": entry.get("failed_blocks", []),
                    }
                )

            course_payload["periods"][period_code]["students_at_risk"] = sorted(
                grouped_students.values(),
                key=lambda item: (
                    item["student"].get("numero", ""),
                    item["student"].get("nombre_estudiante", ""),
                ),
            )
            course_payload["periods"][period_code]["students_at_risk_count"] = len(
                grouped_students
            )

            course_payload["periods"][period_code]["subjects"] = sorted(
                course_payload["periods"][period_code]["subjects"],
                key=lambda item: (
                    item.get("subject_name", ""),
                    item.get("numero", ""),
                ),
            )

    return sorted(courses_map.values(), key=lambda item: item.get("curso", ""))


def build_tracking_dashboard_data(
    rows: list[dict[str, Any]],
    center_id: Optional[Any] = None,
    school_year: Optional[str] = None,
    ciclo: Optional[str] = None,
    course_name: Optional[str] = None,
    period_code: Optional[str] = None,
    subject_code: Optional[str] = None,
    min_score: float = 70.0,
    teacher_assignments: Optional[list[dict[str, Any]]] = None,
) -> dict[str, Any]:
    """
    Construye el payload completo del dashboard de seguimiento académico.
    """
    raw_entries = build_risk_entries_from_rows(
        rows=rows,
        min_score=min_score,
    )

    filtered_entries = _apply_entry_filters(
        entries=raw_entries,
        course_name=course_name,
        period_code=period_code,
        subject_code=subject_code,
    )

    summary_status = _count_summary_statuses(filtered_entries)
    unique_students_at_risk = _build_unique_students_at_risk(filtered_entries)
    period_cards = _build_period_cards(filtered_entries)
    courses = _group_course_period_subjects(
        entries=filtered_entries,
        teacher_assignments=teacher_assignments,
    )

    detected_subjects = get_detected_academic_subjects(rows)
    detected_subject_codes = [item["subject_code"] for item in detected_subjects]

    dashboard_data = {
        "filters": {
            "center_id": center_id,
            "school_year": school_year,
            "ciclo": ciclo,
            "curso": course_name,
            "periodo": period_code,
            "asignatura": subject_code,
            "min_score": min_score,
        },
        "metadata": {
            "courses_detected": _extract_detected_courses(raw_entries),
            "periods_detected": get_supported_period_codes(),
            "subjects_detected": detected_subject_codes,
            "subjects_catalog": detected_subjects,
            "entries_total": len(filtered_entries),
        },
        "summary": {
            "status": summary_status,
            "risk": {
                "students_at_risk_count": len(unique_students_at_risk),
                "failed_competencies_count": sum(
                    int(entry.get("failed_blocks_count", 0))
                    for entry in filtered_entries
                ),
            },
            "period_cards": period_cards,
        },
        "courses": courses,
        "students_at_risk": unique_students_at_risk,
        "status_reference": DASHBOARD_STATUS_REFERENCE,
        "teacher_assignments": teacher_assignments or [],
        "audit_and_recovery": {
            "enabled": False,
            "message": (
                "La auditoría académica y el seguimiento de recuperación "
                "se integrarán en una etapa posterior del módulo."
            ),
        },
    }

    return dashboard_data