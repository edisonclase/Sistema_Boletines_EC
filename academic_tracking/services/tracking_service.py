"""
tracking_service.py

Servicio principal de construcción del dashboard del módulo academic_tracking.

Versión simplificada y operativa:
- prioriza estudiantes afectados
- reduce tablas pesadas
- mantiene seguimiento de recuperación
- deja el payload listo para un dashboard minimalista
"""

from __future__ import annotations

from typing import Any, Optional

from .parsing_service import (
    get_detected_academic_subjects,
    get_supported_period_codes,
)
from .risk_service import (
    PERIOD_STATUS_COMPROMISED,
    build_risk_entries_from_rows,
)


PERIOD_SEQUENCE = ["P1", "P2", "P3", "P4"]
NEXT_PERIOD_MAP = {
    "P1": "P2",
    "P2": "P3",
    "P3": "P4",
    "P4": None,
}


def _normalize_filter_value(value: Optional[Any]) -> Optional[str]:
    if value is None:
        return None

    text = str(value).strip()
    if not text:
        return None

    return text


def _safe_int_for_sort(value: Any) -> tuple[int, str]:
    text = str(value or "").strip()

    if not text:
        return (999999999, "")

    try:
        return (int(text), text)
    except ValueError:
        return (999999999, text)


def _extract_detected_courses(entries: list[dict[str, Any]]) -> list[str]:
    return sorted(
        {
            str(entry.get("curso", "")).strip()
            for entry in entries
            if str(entry.get("curso", "")).strip()
        }
    )


def _status_matches_filter(entry_status: str, filter_status: Optional[str]) -> bool:
    normalized = _normalize_filter_value(filter_status)
    if not normalized:
        return True

    normalized = normalized.lower()

    if normalized == "en_riesgo":
        return entry_status == "en_riesgo"

    if normalized == "no_recuperado":
        return entry_status == "no_recuperado"

    if normalized == "pendiente":
        return entry_status == "pendiente"

    return True


def _has_next_period_publication(
    student_subject_entries: dict[str, dict[str, Any]],
    next_period_code: Optional[str],
) -> bool:
    if not next_period_code:
        return False

    next_entry = student_subject_entries.get(next_period_code)
    if not next_entry:
        return False

    return int(next_entry.get("reported_blocks_count", 0)) > 0


def _build_recovery_follow_up(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], dict[str, dict[str, Any]]] = {}

    for entry in entries:
        key = (
            str(entry.get("student_id", "")).strip(),
            str(entry.get("subject_code", "")).strip(),
        )
        period = str(entry.get("period_code", "")).strip()

        if key not in grouped:
            grouped[key] = {}

        grouped[key][period] = entry

    rows: list[dict[str, Any]] = []

    for (_, _), period_map in grouped.items():
        for source_period in PERIOD_SEQUENCE:
            source_entry = period_map.get(source_period)
            if not source_entry:
                continue

            failed_blocks = source_entry.get("failed_blocks", [])
            if not failed_blocks:
                continue

            next_period = NEXT_PERIOD_MAP.get(source_period)
            has_next_publication = _has_next_period_publication(period_map, next_period)

            for failed_block in failed_blocks:
                if has_next_publication:
                    recovery_status = "no_recuperado"
                    recovery_status_label = f"No recuperó {source_period}"
                else:
                    recovery_status = "pendiente"
                    recovery_status_label = f"Pendiente de validar {source_period}"

                rows.append(
                    {
                        "numero": source_entry.get("numero", ""),
                        "student_id": source_entry.get("student_id", ""),
                        "student_name": source_entry.get("student_name", ""),
                        "course_name": source_entry.get("curso", ""),
                        "subject_code": source_entry.get("subject_code", ""),
                        "subject_name": source_entry.get("subject_name", ""),
                        "source_period": source_period,
                        "checked_at_period": next_period,
                        "block_code": failed_block.get("block_code", ""),
                        "block_label": failed_block.get("block_label", ""),
                        "original_score": failed_block.get("score"),
                        "current_score": failed_block.get("score"),
                        "recovery_status": recovery_status,
                        "recovery_status_label": recovery_status_label,
                    }
                )

    return sorted(
        rows,
        key=lambda item: (
            str(item.get("course_name", "")).strip(),
            _safe_int_for_sort(item.get("numero", "")),
            str(item.get("student_id", "")).strip(),
            str(item.get("subject_name", "")).strip(),
            str(item.get("source_period", "")).strip(),
            str(item.get("block_code", "")).strip(),
        ),
    )


def _build_operational_rows(
    entries: list[dict[str, Any]],
    recovery_follow_up: list[dict[str, Any]],
    teacher_assignments: Optional[list[dict[str, Any]]] = None,
    student_status: Optional[str] = None,
) -> list[dict[str, Any]]:
    teacher_lookup: dict[tuple[str, str], str] = {}

    if teacher_assignments:
        for item in teacher_assignments:
            course_name = str(item.get("course_name", "")).strip()
            subject_code = str(item.get("subject_code", "")).strip()
            teacher_name = str(item.get("teacher_name", "")).strip()

            if course_name and subject_code and teacher_name:
                teacher_lookup[(course_name, subject_code)] = teacher_name

    recovery_index: set[tuple[str, str, str]] = set()
    for item in recovery_follow_up:
        if item.get("recovery_status") == "no_recuperado":
            recovery_index.add(
                (
                    str(item.get("student_id", "")).strip(),
                    str(item.get("subject_code", "")).strip(),
                    str(item.get("source_period", "")).strip(),
                )
            )

    rows: list[dict[str, Any]] = []

    for entry in entries:
        if entry.get("period_status") != PERIOD_STATUS_COMPROMISED:
            continue

        student_id = str(entry.get("student_id", "")).strip()
        subject_code = str(entry.get("subject_code", "")).strip()
        period_code = str(entry.get("period_code", "")).strip()
        course_name = str(entry.get("curso", "")).strip()

        failed_blocks = entry.get("failed_blocks", [])
        failed_block_codes = [block.get("block_code", "") for block in failed_blocks if block.get("block_code")]

        if (student_id, subject_code, period_code) in recovery_index:
            derived_status = "no_recuperado"
            derived_status_label = "No recuperó"
        else:
            next_period = NEXT_PERIOD_MAP.get(period_code)
            has_next_publication = False

            # determinación simple para versión actual
            for candidate in entries:
                if (
                    str(candidate.get("student_id", "")).strip() == student_id
                    and str(candidate.get("subject_code", "")).strip() == subject_code
                    and str(candidate.get("period_code", "")).strip() == str(next_period or "").strip()
                    and int(candidate.get("reported_blocks_count", 0)) > 0
                ):
                    has_next_publication = True
                    break

            if has_next_publication:
                derived_status = "no_recuperado"
                derived_status_label = "No recuperó"
            else:
                derived_status = "en_riesgo"
                derived_status_label = "En riesgo"

        if not _status_matches_filter(derived_status, student_status):
            continue

        rows.append(
            {
                "numero": entry.get("numero", ""),
                "student_id": student_id,
                "student_name": entry.get("student_name", ""),
                "course_name": course_name,
                "subject_code": subject_code,
                "subject_name": entry.get("subject_name", ""),
                "period_code": period_code,
                "failed_blocks": failed_blocks,
                "failed_blocks_count": int(entry.get("failed_blocks_count", 0)),
                "failed_block_codes": failed_block_codes,
                "score_values": [block.get("score") for block in failed_blocks if block.get("score") is not None],
                "lowest_score": min(
                    [block.get("score") for block in failed_blocks if block.get("score") is not None],
                    default=None,
                ),
                "status": derived_status,
                "status_label": derived_status_label,
                "teacher_name": teacher_lookup.get((course_name, subject_code), ""),
            }
        )

    return sorted(
        rows,
        key=lambda item: (
            str(item.get("course_name", "")).strip(),
            _safe_int_for_sort(item.get("numero", "")),
            str(item.get("student_id", "")).strip(),
            str(item.get("subject_name", "")).strip(),
            str(item.get("period_code", "")).strip(),
        ),
    )


def _apply_operational_filters(
    entries: list[dict[str, Any]],
    course_name: Optional[str] = None,
    period_code: Optional[str] = None,
    subject_code: Optional[str] = None,
) -> list[dict[str, Any]]:
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


def build_tracking_dashboard_data(
    rows: list[dict[str, Any]],
    center_id: Optional[Any] = None,
    school_year: Optional[str] = None,
    ciclo: Optional[str] = None,
    course_name: Optional[str] = None,
    period_code: Optional[str] = None,
    subject_code: Optional[str] = None,
    student_status: Optional[str] = None,
    min_score: float = 70.0,
    teacher_assignments: Optional[list[dict[str, Any]]] = None,
) -> dict[str, Any]:
    raw_entries = build_risk_entries_from_rows(
        rows=rows,
        min_score=min_score,
    )

    filtered_entries = _apply_operational_filters(
        entries=raw_entries,
        course_name=course_name,
        period_code=period_code,
        subject_code=subject_code,
    )

    recovery_follow_up = _build_recovery_follow_up(filtered_entries)

    operational_rows = _build_operational_rows(
        entries=filtered_entries,
        recovery_follow_up=recovery_follow_up,
        teacher_assignments=teacher_assignments,
        student_status=student_status,
    )

    detected_subjects = get_detected_academic_subjects(rows)
    detected_subject_codes = [item["subject_code"] for item in detected_subjects]

    students_affected = {
        (str(item.get("student_id", "")).strip(), str(item.get("course_name", "")).strip())
        for item in operational_rows
    }

    courses_with_cases = {
        str(item.get("course_name", "")).strip()
        for item in operational_rows
        if str(item.get("course_name", "")).strip()
    }

    no_recuperados_count = sum(
        1 for item in operational_rows if item.get("status") == "no_recuperado"
    )

    dashboard_data = {
        "filters": {
            "center_id": center_id,
            "school_year": school_year,
            "ciclo": ciclo,
            "curso": course_name,
            "periodo": period_code,
            "asignatura": subject_code,
            "estado": student_status,
            "min_score": min_score,
        },
        "metadata": {
            "courses_detected": _extract_detected_courses(raw_entries),
            "periods_detected": get_supported_period_codes(),
            "subjects_detected": detected_subject_codes,
            "subjects_catalog": detected_subjects,
            "entries_total": len(operational_rows),
        },
        "summary": {
            "cards": {
                "total_cases": len(operational_rows),
                "students_affected": len(students_affected),
                "no_recuperados": no_recuperados_count,
                "courses_with_cases": len(courses_with_cases),
            }
        },
        "operational_rows": operational_rows,
        "recovery_follow_up": recovery_follow_up,
        "teacher_assignments": teacher_assignments or [],
        "audit_and_recovery": {
            "enabled": True,
            "message": (
                "El seguimiento mostrado es operativo y provisional. "
                "La confirmación total de recuperación requerirá historial o "
                "campos explícitos de recuperación por bloque."
            ),
        },
    }

    return dashboard_data