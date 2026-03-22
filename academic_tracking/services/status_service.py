"""
status_service.py

Servicio para calcular el estado de reporte académico por asignatura y período.

Estados esperados:
- REPORTADO: la asignatura tiene valores cargados para todos los estudiantes esperados del curso
- PARCIAL: la asignatura tiene algunos valores cargados, pero no en cobertura completa
- PENDIENTE: no hay valores cargados para esa asignatura y período

Notas:
- Este servicio no toca PDF ni boletines
- Trabaja sobre la estructura del parsing_service
- Está preparado para filtros por curso, período y asignatura
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .parsing_service import (
    PERIODS,
    SUBJECTS,
    filter_rows_by_course,
    get_available_courses,
    get_row_value,
    normalize_course_name,
    row_count_reported_competencies_for_subject_period,
    row_has_any_reported_value_for_subject_period,
)


STATUS_REPORTADO = "REPORTADO"
STATUS_PARCIAL = "PARCIAL"
STATUS_PENDIENTE = "PENDIENTE"


def calculate_subject_period_status_for_rows(
    rows: List[Dict[str, Any]],
    subject_code: str,
    period_code: str,
    subject_period_map: Dict[str, Dict[str, List[str]]],
) -> Dict[str, Any]:
    """
    Calcula el estado de una asignatura en un período dado para un conjunto de filas.

    Regla:
    - PENDIENTE: ninguna fila tiene valores reportados
    - PARCIAL: algunas filas tienen valores, pero no todas
    - REPORTADO: todas las filas tienen al menos una competencia reportada

    Nota:
    Esta primera versión usa una lógica conservadora y práctica.
    Más adelante se puede endurecer para exigir todas las competencias completas.
    """
    total_students = len(rows)

    if total_students == 0:
        return {
            "subject_code": subject_code,
            "subject_name": SUBJECTS.get(subject_code, subject_code),
            "period": period_code,
            "status": STATUS_PENDIENTE,
            "total_students": 0,
            "students_with_any_report": 0,
            "students_without_report": 0,
            "reported_competencies_count": 0,
            "expected_competencies_count": 0,
            "coverage_pct": 0.0,
        }

    students_with_any_report = 0
    reported_competencies_count = 0

    expected_competencies_per_student = len(
        subject_period_map.get(subject_code, {}).get(period_code, [])
    )
    expected_competencies_count = total_students * expected_competencies_per_student

    for row in rows:
        has_any_report = row_has_any_reported_value_for_subject_period(
            row=row,
            subject_code=subject_code,
            period_code=period_code,
            subject_period_map=subject_period_map,
        )
        if has_any_report:
            students_with_any_report += 1

        reported_competencies_count += row_count_reported_competencies_for_subject_period(
            row=row,
            subject_code=subject_code,
            period_code=period_code,
            subject_period_map=subject_period_map,
        )

    students_without_report = total_students - students_with_any_report

    if students_with_any_report == 0:
        status = STATUS_PENDIENTE
    elif students_with_any_report < total_students:
        status = STATUS_PARCIAL
    else:
        status = STATUS_REPORTADO

    coverage_pct = (
        round((reported_competencies_count / expected_competencies_count) * 100, 2)
        if expected_competencies_count > 0
        else 0.0
    )

    return {
        "subject_code": subject_code,
        "subject_name": SUBJECTS.get(subject_code, subject_code),
        "period": period_code,
        "status": status,
        "total_students": total_students,
        "students_with_any_report": students_with_any_report,
        "students_without_report": students_without_report,
        "reported_competencies_count": reported_competencies_count,
        "expected_competencies_count": expected_competencies_count,
        "coverage_pct": coverage_pct,
    }


def calculate_course_status_summary(
    rows: List[Dict[str, Any]],
    subject_period_map: Dict[str, Dict[str, List[str]]],
    course_name: str,
    selected_periods: Optional[List[str]] = None,
    selected_subjects: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Calcula el resumen de estado de reporte para un curso.
    """
    course_rows = filter_rows_by_course(rows, course_name)
    normalized_course = normalize_course_name(course_name)

    periods = selected_periods or list(PERIODS)
    subjects = selected_subjects or list(subject_period_map.keys())

    periods_summary: Dict[str, Any] = {}

    for period_code in periods:
        subject_statuses: List[Dict[str, Any]] = []

        for subject_code in subjects:
            if subject_code not in subject_period_map:
                continue

            status_data = calculate_subject_period_status_for_rows(
                rows=course_rows,
                subject_code=subject_code,
                period_code=period_code,
                subject_period_map=subject_period_map,
            )
            subject_statuses.append(status_data)

        periods_summary[period_code] = {
            "subjects": subject_statuses,
            "reported_subjects": [
                item for item in subject_statuses if item["status"] == STATUS_REPORTADO
            ],
            "partial_subjects": [
                item for item in subject_statuses if item["status"] == STATUS_PARCIAL
            ],
            "pending_subjects": [
                item for item in subject_statuses if item["status"] == STATUS_PENDIENTE
            ],
            "totals": {
                "reported": sum(
                    1 for item in subject_statuses if item["status"] == STATUS_REPORTADO
                ),
                "partial": sum(
                    1 for item in subject_statuses if item["status"] == STATUS_PARCIAL
                ),
                "pending": sum(
                    1 for item in subject_statuses if item["status"] == STATUS_PENDIENTE
                ),
            },
        }

    return {
        "curso": normalized_course,
        "total_students": len(course_rows),
        "periods": periods_summary,
    }


def calculate_all_courses_status_summary(
    rows: List[Dict[str, Any]],
    subject_period_map: Dict[str, Dict[str, List[str]]],
    selected_periods: Optional[List[str]] = None,
    selected_subjects: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Calcula el resumen de estado de reporte para todos los cursos detectados.
    """
    courses = get_available_courses(rows)
    course_summaries = []

    for course_name in courses:
        summary = calculate_course_status_summary(
            rows=rows,
            subject_period_map=subject_period_map,
            course_name=course_name,
            selected_periods=selected_periods,
            selected_subjects=selected_subjects,
        )
        course_summaries.append(summary)

    return {
        "courses": course_summaries,
        "course_count": len(course_summaries),
    }


def build_status_dashboard_data(
    parsed_data: Dict[str, Any],
    course_name: Optional[str] = None,
    period_code: Optional[str] = None,
    subject_code: Optional[str] = None,
    center_id: Optional[Any] = None,
    school_year: Optional[str] = None,
    ciclo: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Punto de entrada principal del servicio.

    Recibe la salida de parse_academic_rows() y devuelve una estructura lista
    para que tracking_service o routes la consuman.
    """
    rows = parsed_data.get("rows", [])
    metadata = parsed_data.get("metadata", {})
    subject_period_map = metadata.get("subject_period_map", {})

    selected_periods = [period_code] if period_code else metadata.get("periods_detected", [])
    selected_subjects = [subject_code] if subject_code else metadata.get("subjects_detected", [])

    if course_name:
        summary = calculate_course_status_summary(
            rows=rows,
            subject_period_map=subject_period_map,
            course_name=course_name,
            selected_periods=selected_periods,
            selected_subjects=selected_subjects,
        )
        courses_data = [summary]
    else:
        all_courses = calculate_all_courses_status_summary(
            rows=rows,
            subject_period_map=subject_period_map,
            selected_periods=selected_periods,
            selected_subjects=selected_subjects,
        )
        courses_data = all_courses["courses"]

    return {
        "filters": {
            "center_id": center_id,
            "school_year": school_year,
            "ciclo": ciclo,
            "curso": normalize_course_name(course_name) if course_name else None,
            "periodo": period_code,
            "asignatura": subject_code,
        },
        "metadata": {
            "subjects_detected": metadata.get("subjects_detected", []),
            "periods_detected": metadata.get("periods_detected", []),
            "courses_detected": metadata.get("courses_detected", []),
        },
        "courses": courses_data,
    }