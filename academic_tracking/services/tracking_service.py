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
    COMPETENCY_BLOCK_LABELS,
    get_detected_academic_subjects,
    get_supported_block_codes,
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


def _student_sort_key_from_entry(entry: dict[str, Any]) -> tuple[Any, ...]:
    return (
        _safe_int_for_sort(entry.get("numero", "")),
        str(entry.get("student_id", "")).strip(),
        str(entry.get("student_name", "")).strip(),
    )


def _student_sort_key_from_student_payload(student_payload: dict[str, Any]) -> tuple[Any, ...]:
    student = student_payload.get("student", {})

    return (
        _safe_int_for_sort(student.get("numero", "")),
        str(student.get("id_estudiante", "")).strip(),
        str(student.get("nombre_estudiante", "")).strip(),
    )


def _apply_entry_filters(
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


def _extract_detected_courses(entries: list[dict[str, Any]]) -> list[str]:
    return sorted(
        {
            str(entry.get("curso", "")).strip()
            for entry in entries
            if str(entry.get("curso", "")).strip()
        }
    )


def _count_summary_statuses(entries: list[dict[str, Any]]) -> dict[str, int]:
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
        key=_student_sort_key_from_student_payload,
    )


def _build_period_cards(entries: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
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
                key=_student_sort_key_from_student_payload,
            )
            course_payload["periods"][period_code]["students_at_risk_count"] = len(
                grouped_students
            )

            course_payload["periods"][period_code]["subjects"] = sorted(
                course_payload["periods"][period_code]["subjects"],
                key=lambda item: (
                    item.get("subject_name", ""),
                    _safe_int_for_sort(item.get("numero", "")),
                    str(item.get("student_id", "")).strip(),
                    str(item.get("student_name", "")).strip(),
                ),
            )

    return sorted(courses_map.values(), key=lambda item: item.get("curso", ""))


def _build_subject_block_summary(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str], dict[str, Any]] = {}

    for entry in entries:
        course_name = str(entry.get("curso", "")).strip()
        period_code = str(entry.get("period_code", "")).strip()
        subject_code = str(entry.get("subject_code", "")).strip()
        subject_name = str(entry.get("subject_name", "")).strip()

        if not course_name or not period_code or not subject_code:
            continue

        group_key = (course_name, period_code, subject_code)

        if group_key not in grouped:
            grouped[group_key] = {
                "course_name": course_name,
                "period_code": period_code,
                "subject_code": subject_code,
                "subject_name": subject_name,
                "students_affected": set(),
                "students_passed": set(),
                "blocks": {
                    block_code: {
                        "block_code": block_code,
                        "block_label": COMPETENCY_BLOCK_LABELS.get(block_code, block_code),
                        "affected_students": set(),
                        "passed_students": set(),
                        "affected_student_details": [],
                    }
                    for block_code in get_supported_block_codes()
                },
            }

        student_payload = {
            "numero": entry.get("numero", ""),
            "student_id": entry.get("student_id", ""),
            "student_name": entry.get("student_name", ""),
            "course_name": course_name,
            "subject_code": subject_code,
            "subject_name": subject_name,
            "period_code": period_code,
        }

        failed_blocks = entry.get("failed_blocks", [])
        failed_block_codes = {
            block.get("block_code", "")
            for block in failed_blocks
            if block.get("block_code")
        }

        if failed_block_codes:
            grouped[group_key]["students_affected"].add(entry.get("student_id", ""))
        else:
            grouped[group_key]["students_passed"].add(entry.get("student_id", ""))

        for block_code in get_supported_block_codes():
            block_bucket = grouped[group_key]["blocks"][block_code]

            if block_code in failed_block_codes:
                block_bucket["affected_students"].add(entry.get("student_id", ""))

                failed_block_detail = next(
                    (
                        block
                        for block in failed_blocks
                        if block.get("block_code") == block_code
                    ),
                    None,
                )

                block_bucket["affected_student_details"].append(
                    {
                        "numero": student_payload["numero"],
                        "student_id": student_payload["student_id"],
                        "student_name": student_payload["student_name"],
                        "score": failed_block_detail.get("score") if failed_block_detail else None,
                    }
                )
            elif entry.get("all_blocks_reported"):
                block_bucket["passed_students"].add(entry.get("student_id", ""))

    summary_rows: list[dict[str, Any]] = []

    for _, payload in grouped.items():
        blocks_output: dict[str, Any] = {}

        for block_code, block_bucket in payload["blocks"].items():
            affected_details_sorted = sorted(
                block_bucket["affected_student_details"],
                key=lambda item: (
                    _safe_int_for_sort(item.get("numero", "")),
                    str(item.get("student_id", "")).strip(),
                    str(item.get("student_name", "")).strip(),
                ),
            )

            blocks_output[block_code] = {
                "block_code": block_code,
                "block_label": block_bucket["block_label"],
                "affected_students_count": len(block_bucket["affected_students"]),
                "passed_students_count": len(block_bucket["passed_students"]),
                "affected_students": affected_details_sorted,
            }

        summary_rows.append(
            {
                "course_name": payload["course_name"],
                "period_code": payload["period_code"],
                "subject_code": payload["subject_code"],
                "subject_name": payload["subject_name"],
                "students_affected_count": len(payload["students_affected"]),
                "students_passed_count": len(payload["students_passed"]),
                "blocks": blocks_output,
            }
        )

    return sorted(
        summary_rows,
        key=lambda item: (
            item.get("course_name", ""),
            item.get("period_code", ""),
            item.get("subject_name", ""),
        ),
    )


def _build_affected_students(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    affected_entries = [
        entry for entry in entries
        if entry.get("period_status") == PERIOD_STATUS_COMPROMISED
    ]

    rows: list[dict[str, Any]] = []

    for entry in affected_entries:
        rows.append(
            {
                "numero": entry.get("numero", ""),
                "student_id": entry.get("student_id", ""),
                "student_name": entry.get("student_name", ""),
                "course_name": entry.get("curso", ""),
                "subject_code": entry.get("subject_code", ""),
                "subject_name": entry.get("subject_name", ""),
                "period_code": entry.get("period_code", ""),
                "affected_blocks_count": entry.get("failed_blocks_count", 0),
                "affected_blocks": entry.get("failed_blocks", []),
            }
        )

    return sorted(
        rows,
        key=lambda item: (
            _safe_int_for_sort(item.get("numero", "")),
            str(item.get("student_id", "")).strip(),
            str(item.get("student_name", "")).strip(),
            str(item.get("subject_name", "")).strip(),
            str(item.get("period_code", "")).strip(),
        ),
    )


def _has_next_period_publication(
    student_subject_entries: dict[str, dict[str, Any]],
    next_period_code: Optional[str],
) -> bool:
    """
    Determina si ya existe publicación del período siguiente para la misma
    asignatura del mismo estudiante.
    """
    if not next_period_code:
        return False

    next_entry = student_subject_entries.get(next_period_code)
    if not next_entry:
        return False

    return int(next_entry.get("reported_blocks_count", 0)) > 0


def _build_recovery_follow_up(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Construye seguimiento provisional de recuperación.

    Regla actual:
    - Si un bloque del período anterior sigue < 70
    - y ya existe publicación del período siguiente
    => se marca como "No recuperó"

    Limitación honesta:
    - Sin historial o campos explícitos de recuperación por bloque,
      no podemos reconstruir recuperación exitosa con total certeza.
    """
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
                    recovery_status = "not_recovered"
                    recovery_status_label = f"No recuperó {source_period}"
                else:
                    recovery_status = "pending_validation"
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
            _safe_int_for_sort(item.get("numero", "")),
            str(item.get("student_id", "")).strip(),
            str(item.get("student_name", "")).strip(),
            str(item.get("subject_name", "")).strip(),
            str(item.get("source_period", "")).strip(),
            str(item.get("block_code", "")).strip(),
        ),
    )


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
        "subject_block_summary": _build_subject_block_summary(filtered_entries),
        "affected_students": _build_affected_students(filtered_entries),
        "recovery_follow_up": _build_recovery_follow_up(filtered_entries),
        "courses": courses,
        "students_at_risk": unique_students_at_risk,
        "status_reference": DASHBOARD_STATUS_REFERENCE,
        "teacher_assignments": teacher_assignments or [],
        "audit_and_recovery": {
            "enabled": True,
            "message": (
                "El seguimiento provisional de recuperación ya está disponible. "
                "La recuperación confirmada al 100% requerirá historial o campos "
                "explícitos de recuperación por bloque."
            ),
        },
    }

    return dashboard_data