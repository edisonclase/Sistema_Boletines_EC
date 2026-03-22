"""
risk_service.py

Servicio para detectar estudiantes en riesgo académico por período
y contabilizar competencias reprobadas.

Objetivos:
- Identificar estudiantes que se quedaron en P1, P2, P3 y P4
- Contar cuántas competencias reprobadas tiene cada estudiante por asignatura y período
- Generar resúmenes por curso, período y asignatura
- Mantener estructura preparada para multi-centro

Regla inicial:
- Un estudiante está en riesgo en una asignatura/período si al menos una competencia
  del período está por debajo del mínimo de aprobación.
- Un estudiante "se quedó" en un período si tiene al menos una asignatura en riesgo
  en ese período.

Nota:
- Este servicio no toca boletines ni PDFs
- El mínimo de aprobación es parametrizable
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .parsing_service import (
    PERIODS,
    SUBJECTS,
    extract_competency_values_from_row,
    filter_rows_by_course,
    get_available_courses,
    get_student_base_info,
    normalize_course_name,
)


MIN_APPROVAL_SCORE = 70.0


def is_failed_competency(value: Optional[float], min_score: float = DEFAULT_MIN_COMPETENCY_SCORE) -> bool:
    """
    Determina si una competencia está reprobada.
    """
    if value is None:
        return False
    return value < min_score


def get_failed_competencies_for_student_subject_period(
    row: Dict[str, Any],
    subject_code: str,
    period_code: str,
    subject_period_map: Dict[str, Dict[str, List[str]]],
    min_score: float = DEFAULT_MIN_COMPETENCY_SCORE,
) -> Dict[str, Any]:
    """
    Devuelve el detalle de competencias reprobadas de un estudiante
    en una asignatura y período.

    Salida esperada:
    {
        "subject_code": "LEN",
        "subject_name": "Lengua Española",
        "period": "P1",
        "competency_values": {"C1": 65.0, "C2": 80.0, ...},
        "failed_competencies": ["C1", "C3"],
        "failed_count": 2,
        "has_risk": True
    }
    """
    competency_values = extract_competency_values_from_row(
        row=row,
        subject_code=subject_code,
        period_code=period_code,
        subject_period_map=subject_period_map,
    )

    failed_competencies = [
        competency_code
        for competency_code, score in competency_values.items()
        if is_failed_competency(score, min_score=min_score)
    ]

    return {
        "subject_code": subject_code,
        "subject_name": SUBJECTS.get(subject_code, subject_code),
        "period": period_code,
        "competency_values": competency_values,
        "failed_competencies": failed_competencies,
        "failed_count": len(failed_competencies),
        "has_risk": len(failed_competencies) > 0,
    }


def get_student_risk_for_period(
    row: Dict[str, Any],
    period_code: str,
    subject_period_map: Dict[str, Dict[str, List[str]]],
    selected_subjects: Optional[List[str]] = None,
    min_score: float = DEFAULT_MIN_COMPETENCY_SCORE,
) -> Dict[str, Any]:
    """
    Evalúa el riesgo de un estudiante en un período completo.

    Un estudiante está en riesgo en el período si tiene al menos una asignatura
    con una o más competencias reprobadas.
    """
    subjects = selected_subjects or list(subject_period_map.keys())
    subject_risks: List[Dict[str, Any]] = []

    for subject_code in subjects:
        if subject_code not in subject_period_map:
            continue

        subject_risk = get_failed_competencies_for_student_subject_period(
            row=row,
            subject_code=subject_code,
            period_code=period_code,
            subject_period_map=subject_period_map,
            min_score=min_score,
        )

        if subject_risk["has_risk"]:
            subject_risks.append(subject_risk)

    total_failed_competencies = sum(item["failed_count"] for item in subject_risks)

    return {
        "student": get_student_base_info(row),
        "period": period_code,
        "subjects_at_risk": subject_risks,
        "subjects_at_risk_count": len(subject_risks),
        "failed_competencies_count": total_failed_competencies,
        "is_at_risk": len(subject_risks) > 0,
    }


def get_students_at_risk_for_course_period(
    rows: List[Dict[str, Any]],
    course_name: str,
    period_code: str,
    subject_period_map: Dict[str, Dict[str, List[str]]],
    selected_subjects: Optional[List[str]] = None,
    min_score: float = DEFAULT_MIN_COMPETENCY_SCORE,
) -> Dict[str, Any]:
    """
    Obtiene todos los estudiantes en riesgo para un curso y período.
    """
    course_rows = filter_rows_by_course(rows, course_name)
    normalized_course = normalize_course_name(course_name)

    students_risk_details: List[Dict[str, Any]] = []

    for row in course_rows:
        student_risk = get_student_risk_for_period(
            row=row,
            period_code=period_code,
            subject_period_map=subject_period_map,
            selected_subjects=selected_subjects,
            min_score=min_score,
        )

        if student_risk["is_at_risk"]:
            students_risk_details.append(student_risk)

    total_failed_competencies = sum(
        item["failed_competencies_count"] for item in students_risk_details
    )

    return {
        "curso": normalized_course,
        "period": period_code,
        "total_students": len(course_rows),
        "students_at_risk": students_risk_details,
        "students_at_risk_count": len(students_risk_details),
        "failed_competencies_count": total_failed_competencies,
    }


def summarize_subject_risk_for_course_period(
    rows: List[Dict[str, Any]],
    course_name: str,
    period_code: str,
    subject_period_map: Dict[str, Dict[str, List[str]]],
    selected_subjects: Optional[List[str]] = None,
    min_score: float = DEFAULT_MIN_COMPETENCY_SCORE,
) -> List[Dict[str, Any]]:
    """
    Resume el riesgo por asignatura dentro de un curso y período.
    """
    course_rows = filter_rows_by_course(rows, course_name)
    subjects = selected_subjects or list(subject_period_map.keys())

    summary: List[Dict[str, Any]] = []

    for subject_code in subjects:
        if subject_code not in subject_period_map:
            continue

        students_with_risk = 0
        failed_competencies_count = 0

        for row in course_rows:
            subject_risk = get_failed_competencies_for_student_subject_period(
                row=row,
                subject_code=subject_code,
                period_code=period_code,
                subject_period_map=subject_period_map,
                min_score=min_score,
            )

            if subject_risk["has_risk"]:
                students_with_risk += 1
                failed_competencies_count += subject_risk["failed_count"]

        summary.append(
            {
                "subject_code": subject_code,
                "subject_name": SUBJECTS.get(subject_code, subject_code),
                "period": period_code,
                "students_at_risk_count": students_with_risk,
                "failed_competencies_count": failed_competencies_count,
            }
        )

    return summary


def calculate_course_risk_summary(
    rows: List[Dict[str, Any]],
    subject_period_map: Dict[str, Dict[str, List[str]]],
    course_name: str,
    selected_periods: Optional[List[str]] = None,
    selected_subjects: Optional[List[str]] = None,
    min_score: float = DEFAULT_MIN_COMPETENCY_SCORE,
) -> Dict[str, Any]:
    """
    Calcula el resumen de riesgo completo para un curso.
    """
    normalized_course = normalize_course_name(course_name)
    periods = selected_periods or list(PERIODS)

    periods_summary: Dict[str, Any] = {}

    for period_code in periods:
        course_period_risk = get_students_at_risk_for_course_period(
            rows=rows,
            course_name=normalized_course,
            period_code=period_code,
            subject_period_map=subject_period_map,
            selected_subjects=selected_subjects,
            min_score=min_score,
        )

        subject_summary = summarize_subject_risk_for_course_period(
            rows=rows,
            course_name=normalized_course,
            period_code=period_code,
            subject_period_map=subject_period_map,
            selected_subjects=selected_subjects,
            min_score=min_score,
        )

        periods_summary[period_code] = {
            "students_at_risk": course_period_risk["students_at_risk"],
            "students_at_risk_count": course_period_risk["students_at_risk_count"],
            "failed_competencies_count": course_period_risk["failed_competencies_count"],
            "subjects_summary": subject_summary,
        }

    return {
        "curso": normalized_course,
        "periods": periods_summary,
    }


def calculate_all_courses_risk_summary(
    rows: List[Dict[str, Any]],
    subject_period_map: Dict[str, Dict[str, List[str]]],
    selected_periods: Optional[List[str]] = None,
    selected_subjects: Optional[List[str]] = None,
    min_score: float = DEFAULT_MIN_COMPETENCY_SCORE,
) -> Dict[str, Any]:
    """
    Calcula el resumen de riesgo para todos los cursos detectados.
    """
    courses = get_available_courses(rows)
    course_summaries: List[Dict[str, Any]] = []

    for course_name in courses:
        summary = calculate_course_risk_summary(
            rows=rows,
            subject_period_map=subject_period_map,
            course_name=course_name,
            selected_periods=selected_periods,
            selected_subjects=selected_subjects,
            min_score=min_score,
        )
        course_summaries.append(summary)

    return {
        "courses": course_summaries,
        "course_count": len(course_summaries),
    }


def build_risk_dashboard_data(
    parsed_data: Dict[str, Any],
    course_name: Optional[str] = None,
    period_code: Optional[str] = None,
    subject_code: Optional[str] = None,
    center_id: Optional[Any] = None,
    school_year: Optional[str] = None,
    ciclo: Optional[str] = None,
    min_score: float = DEFAULT_MIN_COMPETENCY_SCORE,
) -> Dict[str, Any]:
    """
    Punto de entrada principal del servicio.

    Recibe la salida de parse_academic_rows() y devuelve una estructura lista
    para el dashboard de seguimiento académico.
    """
    rows = parsed_data.get("rows", [])
    metadata = parsed_data.get("metadata", {})
    subject_period_map = metadata.get("subject_period_map", {})

    selected_periods = [period_code] if period_code else metadata.get("periods_detected", [])
    selected_subjects = [subject_code] if subject_code else metadata.get("subjects_detected", [])

    if course_name:
        summary = calculate_course_risk_summary(
            rows=rows,
            subject_period_map=subject_period_map,
            course_name=course_name,
            selected_periods=selected_periods,
            selected_subjects=selected_subjects,
            min_score=min_score,
        )
        courses_data = [summary]
    else:
        all_courses = calculate_all_courses_risk_summary(
            rows=rows,
            subject_period_map=subject_period_map,
            selected_periods=selected_periods,
            selected_subjects=selected_subjects,
            min_score=min_score,
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
            "min_score": min_score,
        },
        "metadata": {
            "subjects_detected": metadata.get("subjects_detected", []),
            "periods_detected": metadata.get("periods_detected", []),
            "courses_detected": metadata.get("courses_detected", []),
        },
        "courses": courses_data,
    }