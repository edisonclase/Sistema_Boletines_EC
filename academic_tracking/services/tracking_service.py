"""
tracking_service.py

Servicio orquestador del módulo academic_tracking.

Objetivos:
- Unificar la salida de status_service y risk_service
- Preparar una estructura única para el dashboard de coordinadores
- Mantener filtros listos para multi-centro
- Dejar base preparada para integrar docente_asignatura y auditoría académica
- No tocar nada de boletines web o PDF

Notas de diseño:
- Este archivo NO debe contener lógica pesada duplicada
- Debe apoyarse en parsing_service, status_service y risk_service
- Debe devolver estructuras limpias, predecibles y fáciles de renderizar
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .parsing_service import (
    PERIODS,
    SUBJECTS,
    parse_academic_rows,
)
from .risk_service import (
    MIN_APPROVAL_SCORE,
    build_risk_dashboard_data,
)
from .status_service import (
    STATUS_PARCIAL,
    STATUS_PENDIENTE,
    STATUS_REPORTADO,
    build_status_dashboard_data,
)


def _build_default_teacher_index(
    teacher_assignments: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Dict[str, Any]]:
    """
    Construye un índice rápido para buscar docente por:
    center_id + school_year + ciclo + curso + asignatura_codigo

    Formato de salida:
    {
        "1|2025-2026|Primer Ciclo|1ro A|LEN": {
            "docente_asignatura": "María Pérez",
            "docente_asignatura_id": "15",
            ...
        }
    }
    """
    if not teacher_assignments:
        return {}

    teacher_index: Dict[str, Dict[str, Any]] = {}

    for item in teacher_assignments:
        center_id = item.get("center_id")
        school_year = item.get("school_year")
        ciclo = item.get("ciclo")
        curso = item.get("curso")
        asignatura_codigo = item.get("asignatura_codigo")

        key = _build_teacher_assignment_key(
            center_id=center_id,
            school_year=school_year,
            ciclo=ciclo,
            curso=curso,
            asignatura_codigo=asignatura_codigo,
        )

        teacher_index[key] = item

    return teacher_index


def _build_teacher_assignment_key(
    center_id: Optional[Any],
    school_year: Optional[str],
    ciclo: Optional[str],
    curso: Optional[str],
    asignatura_codigo: Optional[str],
) -> str:
    """
    Crea la llave única del cruce de docente_asignatura.
    """
    return "|".join(
        [
            str(center_id or ""),
            str(school_year or ""),
            str(ciclo or ""),
            str(curso or ""),
            str(asignatura_codigo or ""),
        ]
    )


def _get_teacher_assignment(
    teacher_index: Dict[str, Dict[str, Any]],
    center_id: Optional[Any],
    school_year: Optional[str],
    ciclo: Optional[str],
    curso: Optional[str],
    asignatura_codigo: Optional[str],
) -> Dict[str, Any]:
    """
    Busca el docente asignado a una combinación curso + asignatura.
    Si no existe, devuelve estructura vacía sin romper el flujo.
    """
    key = _build_teacher_assignment_key(
        center_id=center_id,
        school_year=school_year,
        ciclo=ciclo,
        curso=curso,
        asignatura_codigo=asignatura_codigo,
    )
    return teacher_index.get(
        key,
        {
            "docente_asignatura": None,
            "docente_asignatura_id": None,
            "teacher_assignment_found": False,
        },
    )


def _build_status_index(status_dashboard_data: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """
    Convierte la salida de status_service en índice por:
    curso -> período -> asignatura
    """
    index: Dict[str, Dict[str, Any]] = {}

    for course_item in status_dashboard_data.get("courses", []):
        curso = course_item.get("curso")
        periods = course_item.get("periods", {})

        index[curso] = {}

        for period_code, period_payload in periods.items():
            index[curso][period_code] = {}

            for subject_item in period_payload.get("subjects", []):
                subject_code = subject_item.get("subject_code")
                index[curso][period_code][subject_code] = subject_item

    return index


def _build_risk_index(risk_dashboard_data: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """
    Convierte la salida de risk_service en índice por:
    curso -> período
    """
    index: Dict[str, Dict[str, Any]] = {}

    for course_item in risk_dashboard_data.get("courses", []):
        curso = course_item.get("curso")
        periods = course_item.get("periods", {})
        index[curso] = periods

    return index


def _summarize_global_status(status_dashboard_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Resume estados globales de reporte.
    """
    total_reported = 0
    total_partial = 0
    total_pending = 0

    for course_item in status_dashboard_data.get("courses", []):
        for period_payload in course_item.get("periods", {}).values():
            totals = period_payload.get("totals", {})
            total_reported += totals.get("reported", 0)
            total_partial += totals.get("partial", 0)
            total_pending += totals.get("pending", 0)

    return {
        "reported": total_reported,
        "partial": total_partial,
        "pending": total_pending,
    }


def _summarize_global_risk(risk_dashboard_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Resume riesgos globales.
    """
    students_at_risk_count = 0
    failed_competencies_count = 0

    for course_item in risk_dashboard_data.get("courses", []):
        for period_payload in course_item.get("periods", {}).values():
            students_at_risk_count += period_payload.get("students_at_risk_count", 0)
            failed_competencies_count += period_payload.get("failed_competencies_count", 0)

    return {
        "students_at_risk_count": students_at_risk_count,
        "failed_competencies_count": failed_competencies_count,
    }


def _merge_subject_row(
    curso: str,
    period_code: str,
    subject_code: str,
    status_item: Dict[str, Any],
    risk_period_payload: Dict[str, Any],
    teacher_index: Dict[str, Dict[str, Any]],
    center_id: Optional[Any],
    school_year: Optional[str],
    ciclo: Optional[str],
) -> Dict[str, Any]:
    """
    Une en una sola fila:
    - estado de reporte
    - datos de riesgo por asignatura
    - docente asignado
    """
    subjects_summary = risk_period_payload.get("subjects_summary", [])
    matching_subject_risk = next(
        (item for item in subjects_summary if item.get("subject_code") == subject_code),
        {
            "subject_code": subject_code,
            "subject_name": SUBJECTS.get(subject_code, subject_code),
            "period": period_code,
            "students_at_risk_count": 0,
            "failed_competencies_count": 0,
        },
    )

    teacher_assignment = _get_teacher_assignment(
        teacher_index=teacher_index,
        center_id=center_id,
        school_year=school_year,
        ciclo=ciclo,
        curso=curso,
        asignatura_codigo=subject_code,
    )

    return {
        "curso": curso,
        "period": period_code,
        "subject_code": subject_code,
        "subject_name": SUBJECTS.get(subject_code, subject_code),
        "status": status_item.get("status"),
        "status_label": status_item.get("status"),
        "coverage_pct": status_item.get("coverage_pct", 0.0),
        "total_students": status_item.get("total_students", 0),
        "students_with_any_report": status_item.get("students_with_any_report", 0),
        "students_without_report": status_item.get("students_without_report", 0),
        "reported_competencies_count": status_item.get("reported_competencies_count", 0),
        "expected_competencies_count": status_item.get("expected_competencies_count", 0),
        "students_at_risk_count": matching_subject_risk.get("students_at_risk_count", 0),
        "failed_competencies_count": matching_subject_risk.get("failed_competencies_count", 0),
        "docente_asignatura": teacher_assignment.get("docente_asignatura"),
        "docente_asignatura_id": teacher_assignment.get("docente_asignatura_id"),
        "teacher_assignment_found": teacher_assignment.get("teacher_assignment_found", True)
        if "teacher_assignment_found" in teacher_assignment
        else True,
    }


def _build_period_summary_cards(
    status_dashboard_data: Dict[str, Any],
    risk_dashboard_data: Dict[str, Any],
    selected_periods: List[str],
) -> Dict[str, Any]:
    """
    Construye tarjetas resumen por período.
    """
    result: Dict[str, Any] = {}

    for period_code in selected_periods:
        reported = 0
        partial = 0
        pending = 0
        students_at_risk = 0
        failed_competencies = 0

        for course_item in status_dashboard_data.get("courses", []):
            period_payload = course_item.get("periods", {}).get(period_code, {})
            totals = period_payload.get("totals", {})
            reported += totals.get("reported", 0)
            partial += totals.get("partial", 0)
            pending += totals.get("pending", 0)

        for course_item in risk_dashboard_data.get("courses", []):
            period_payload = course_item.get("periods", {}).get(period_code, {})
            students_at_risk += period_payload.get("students_at_risk_count", 0)
            failed_competencies += period_payload.get("failed_competencies_count", 0)

        result[period_code] = {
            "reported_subjects": reported,
            "partial_subjects": partial,
            "pending_subjects": pending,
            "students_at_risk_count": students_at_risk,
            "failed_competencies_count": failed_competencies,
        }

    return result


def _build_course_periods_view(
    status_dashboard_data: Dict[str, Any],
    risk_dashboard_data: Dict[str, Any],
    teacher_index: Dict[str, Dict[str, Any]],
    center_id: Optional[Any],
    school_year: Optional[str],
    ciclo: Optional[str],
) -> List[Dict[str, Any]]:
    """
    Construye la vista principal por curso y período,
    lista para ser renderizada en dashboard.
    """
    status_index = _build_status_index(status_dashboard_data)
    risk_index = _build_risk_index(risk_dashboard_data)

    courses_view: List[Dict[str, Any]] = []

    for course_item in status_dashboard_data.get("courses", []):
        curso = course_item.get("curso")
        periods_payload: Dict[str, Any] = {}

        for period_code, period_payload in course_item.get("periods", {}).items():
            subject_rows: List[Dict[str, Any]] = []

            risk_period_payload = risk_index.get(curso, {}).get(
                period_code,
                {
                    "students_at_risk": [],
                    "students_at_risk_count": 0,
                    "failed_competencies_count": 0,
                    "subjects_summary": [],
                },
            )

            for status_item in period_payload.get("subjects", []):
                subject_code = status_item.get("subject_code")

                merged_row = _merge_subject_row(
                    curso=curso,
                    period_code=period_code,
                    subject_code=subject_code,
                    status_item=status_item,
                    risk_period_payload=risk_period_payload,
                    teacher_index=teacher_index,
                    center_id=center_id,
                    school_year=school_year,
                    ciclo=ciclo,
                )
                subject_rows.append(merged_row)

            periods_payload[period_code] = {
                "subjects": subject_rows,
                "students_at_risk": risk_period_payload.get("students_at_risk", []),
                "students_at_risk_count": risk_period_payload.get("students_at_risk_count", 0),
                "failed_competencies_count": risk_period_payload.get("failed_competencies_count", 0),
                "totals": period_payload.get("totals", {}),
            }

        courses_view.append(
            {
                "curso": curso,
                "total_students": course_item.get("total_students", 0),
                "periods": periods_payload,
            }
        )

    return courses_view


def _build_recovery_placeholder(selected_periods: List[str]) -> Dict[str, Any]:
    """
    Estructura base para futura integración de recuperaciones y auditoría académica.

    Importante:
    - Por ahora es placeholder intencional
    - Deja el dashboard listo para crecer sin romper estructura
    """
    return {
        "enabled": False,
        "message": (
            "La auditoría académica y el seguimiento de recuperaciones "
            "requieren historial de cambios o snapshots de importación."
        ),
        "periods": {
            period_code: {
                "students_recovered_count": 0,
                "students_still_failed_count": 0,
                "recent_changes": [],
            }
            for period_code in selected_periods
        },
    }


def build_tracking_dashboard_data(
    rows: List[Dict[str, Any]],
    center_id: Optional[Any] = None,
    school_year: Optional[str] = None,
    ciclo: Optional[str] = None,
    course_name: Optional[str] = None,
    period_code: Optional[str] = None,
    subject_code: Optional[str] = None,
    min_score: float = MIN_APPROVAL_SCORE,
    teacher_assignments: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """
    Punto de entrada principal del módulo academic_tracking.

    Flujo:
    1. Parsea filas académicas
    2. Construye estado de reporte
    3. Construye riesgo académico
    4. Une ambas salidas en una estructura única
    5. Deja preparada base para docente_asignatura y auditoría

    Parámetros:
    - rows: filas crudas provenientes del import actual
    - center_id: obligatorio a nivel de arquitectura, aunque hoy haya un solo centro
    - school_year: recomendado
    - ciclo: recomendado
    - course_name, period_code, subject_code: filtros
    - min_score: mínimo de aprobación (70 por defecto)
    - teacher_assignments: fuente auxiliar de docente_asignatura
    """
    parsed_data = parse_academic_rows(rows)

    metadata = parsed_data.get("metadata", {})
    selected_periods = [period_code] if period_code else metadata.get("periods_detected", list(PERIODS))
    selected_subjects = [subject_code] if subject_code else metadata.get(
        "subjects_detected",
        list(SUBJECTS.keys()),
    )

    status_dashboard_data = build_status_dashboard_data(
        parsed_data=parsed_data,
        course_name=course_name,
        period_code=period_code,
        subject_code=subject_code,
        center_id=center_id,
        school_year=school_year,
        ciclo=ciclo,
    )

    risk_dashboard_data = build_risk_dashboard_data(
        parsed_data=parsed_data,
        course_name=course_name,
        period_code=period_code,
        subject_code=subject_code,
        center_id=center_id,
        school_year=school_year,
        ciclo=ciclo,
        min_score=min_score,
    )

    teacher_index = _build_default_teacher_index(teacher_assignments)

    courses_view = _build_course_periods_view(
        status_dashboard_data=status_dashboard_data,
        risk_dashboard_data=risk_dashboard_data,
        teacher_index=teacher_index,
        center_id=center_id,
        school_year=school_year,
        ciclo=ciclo,
    )

    global_status_summary = _summarize_global_status(status_dashboard_data)
    global_risk_summary = _summarize_global_risk(risk_dashboard_data)

    dashboard_data = {
        "filters": {
            "center_id": center_id,
            "school_year": school_year,
            "ciclo": ciclo,
            "curso": course_name,
            "periodo": period_code,
            "asignatura": subject_code,
            "min_approval_score": min_score,
        },
        "metadata": {
            "subjects_detected": metadata.get("subjects_detected", []),
            "periods_detected": metadata.get("periods_detected", []),
            "courses_detected": metadata.get("courses_detected", []),
            "row_count": metadata.get("row_count", 0),
        },
        "summary": {
            "status": global_status_summary,
            "risk": global_risk_summary,
            "period_cards": _build_period_summary_cards(
                status_dashboard_data=status_dashboard_data,
                risk_dashboard_data=risk_dashboard_data,
                selected_periods=selected_periods,
            ),
        },
        "courses": courses_view,
        "status_reference": {
            "reported": STATUS_REPORTADO,
            "partial": STATUS_PARCIAL,
            "pending": STATUS_PENDIENTE,
        },
        "teacher_assignments": {
            "enabled": True,
            "source_loaded": bool(teacher_assignments),
            "records_count": len(teacher_assignments or []),
        },
        "audit_and_recovery": _build_recovery_placeholder(selected_periods),
    }

    return dashboard_data