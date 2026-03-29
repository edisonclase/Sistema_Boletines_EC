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

import re
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

CYCLE_OPTIONS = [
    {"value": "Primer Ciclo", "label": "Primer Ciclo"},
    {"value": "Segundo Ciclo", "label": "Segundo Ciclo"},
]

GRADE_LABELS = {
    1: "Primero",
    2: "Segundo",
    3: "Tercero",
    4: "Cuarto",
    5: "Quinto",
    6: "Sexto",
}

DEFAULT_SECTION_DISPLAY_BY_CYCLE = {
    "Primer Ciclo": {
        "A": "A",
        "B": "B",
        "C": "C",
    },
    "Segundo Ciclo": {
        "A": "Servicios de Alojamiento",
        "B": "Atención a Emergencias de Salud",
        "C": "Logística y Transporte",
    },
}


def _normalize_filter_value(value: Optional[Any]) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _safe_int_for_sort(value: Any) -> tuple[int, str]:
    text = str(value or "").strip()

    if not text:
        return (999999999, "")

    try:
        return (int(text), text)
    except ValueError:
        return (999999999, text)


def _split_course_name(course_name: str) -> tuple[str, str]:
    text = str(course_name or "").strip()
    if not text:
        return ("", "")

    parts = text.split()
    if len(parts) >= 2:
        grado = " ".join(parts[:-1]).strip()
        seccion = parts[-1].strip()
        return (grado, seccion)

    return (text, "")


def _extract_grade_number(raw_grade: str) -> Optional[int]:
    text = str(raw_grade or "").strip()
    if not text:
        return None

    match = re.search(r"([1-6])", text)
    if not match:
        return None

    try:
        return int(match.group(1))
    except ValueError:
        return None


def _infer_cycle_from_grade(raw_grade: str) -> Optional[str]:
    grade_number = _extract_grade_number(raw_grade)
    if grade_number is None:
        return None

    if grade_number in {1, 2, 3}:
        return "Primer Ciclo"

    if grade_number in {4, 5, 6}:
        return "Segundo Ciclo"

    return None


def _get_grade_display(raw_grade: str) -> str:
    grade_number = _extract_grade_number(raw_grade)
    if grade_number in GRADE_LABELS:
        return GRADE_LABELS[grade_number]
    return str(raw_grade or "").strip()


def _get_section_display(raw_section: str, ciclo: Optional[str] = None) -> str:
    section = str(raw_section or "").strip()
    if not section:
        return ""

    cycle_key = str(ciclo or "").strip()
    if cycle_key in DEFAULT_SECTION_DISPLAY_BY_CYCLE:
        return DEFAULT_SECTION_DISPLAY_BY_CYCLE[cycle_key].get(section, section)

    return section


def _extract_detected_courses(entries: list[dict[str, Any]]) -> list[str]:
    return sorted(
        {
            str(entry.get("curso", "")).strip()
            for entry in entries
            if str(entry.get("curso", "")).strip()
        }
    )


def _extract_grades_and_sections(
    entries: list[dict[str, Any]],
    selected_cycle: Optional[str] = None,
) -> dict[str, Any]:
    grades_map: dict[str, dict[str, str]] = {}
    sections_map: dict[str, dict[str, Any]] = {}
    sections_by_grade: dict[str, list[dict[str, str]]] = {}

    normalized_selected_cycle = _normalize_filter_value(selected_cycle)

    for entry in entries:
        course_name = str(entry.get("curso", "")).strip()
        raw_grade, raw_section = _split_course_name(course_name)

        if not raw_grade:
            continue

        inferred_cycle = _infer_cycle_from_grade(raw_grade)
        if normalized_selected_cycle and inferred_cycle and inferred_cycle != normalized_selected_cycle:
            continue

        grade_display = _get_grade_display(raw_grade)
        section_display = _get_section_display(raw_section, inferred_cycle)

        if raw_grade not in grades_map:
            grades_map[raw_grade] = {
                "value": raw_grade,
                "label": grade_display,
                "cycle": inferred_cycle or "",
            }

        if raw_section:
            if raw_section not in sections_map:
                sections_map[raw_section] = {
                    "value": raw_section,
                    "label": section_display or raw_section,
                    "cycle": inferred_cycle or "",
                }

            sections_by_grade.setdefault(raw_grade, [])
            existing_values = {item["value"] for item in sections_by_grade[raw_grade]}
            if raw_section not in existing_values:
                sections_by_grade[raw_grade].append(
                    {
                        "value": raw_section,
                        "label": section_display or raw_section,
                    }
                )

    grades_catalog = sorted(
        grades_map.values(),
        key=lambda item: (
            _safe_int_for_sort(_extract_grade_number(item.get("value", "")) or 999)[0],
            item.get("label", ""),
        ),
    )

    sections_catalog = sorted(
        sections_map.values(),
        key=lambda item: item.get("label", ""),
    )

    for raw_grade in sections_by_grade:
        sections_by_grade[raw_grade] = sorted(
            sections_by_grade[raw_grade],
            key=lambda item: item.get("label", ""),
        )

    return {
        "grades_catalog": grades_catalog,
        "sections_catalog": sections_catalog,
        "sections_by_grade": sections_by_grade,
    }


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


def _apply_operational_filters(
    entries: list[dict[str, Any]],
    ciclo: Optional[str] = None,
    course_name: Optional[str] = None,
    grade_name: Optional[str] = None,
    section_name: Optional[str] = None,
    period_code: Optional[str] = None,
    subject_code: Optional[str] = None,
    student_id: Optional[str] = None,
) -> list[dict[str, Any]]:
    filtered = entries

    normalized_cycle = _normalize_filter_value(ciclo)
    normalized_course = _normalize_filter_value(course_name)
    normalized_grade = _normalize_filter_value(grade_name)
    normalized_section = _normalize_filter_value(section_name)
    normalized_period = _normalize_filter_value(period_code)
    normalized_subject = _normalize_filter_value(subject_code)
    normalized_student_id = _normalize_filter_value(student_id)

    if normalized_cycle:
        filtered = [
            entry
            for entry in filtered
            if _infer_cycle_from_grade(_split_course_name(str(entry.get("curso", "")).strip())[0]) == normalized_cycle
        ]

    if normalized_course:
        filtered = [
            entry
            for entry in filtered
            if str(entry.get("curso", "")).strip() == normalized_course
        ]

    if normalized_grade:
        filtered = [
            entry
            for entry in filtered
            if _split_course_name(str(entry.get("curso", "")).strip())[0] == normalized_grade
        ]

    if normalized_section:
        filtered = [
            entry
            for entry in filtered
            if _split_course_name(str(entry.get("curso", "")).strip())[1] == normalized_section
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

    if normalized_student_id:
        filtered = [
            entry
            for entry in filtered
            if str(entry.get("student_id", "")).strip() == normalized_student_id
        ]

    return filtered


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
        student_name = str(entry.get("student_name", "")).strip()
        numero = str(entry.get("numero", "")).strip()

        raw_grade, raw_section = _split_course_name(course_name)
        inferred_cycle = _infer_cycle_from_grade(raw_grade)

        failed_blocks = entry.get("failed_blocks", [])

        if (student_id, subject_code, period_code) in recovery_index:
            derived_status = "no_recuperado"
            derived_status_label = "No recuperó"
        else:
            next_period = NEXT_PERIOD_MAP.get(period_code)
            has_next_publication = False

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
                derived_status_label = "Recuperación pedagógica"

        if not _status_matches_filter(derived_status, student_status):
            continue

        score_values = [
            block.get("score")
            for block in failed_blocks
            if block.get("score") is not None
        ]

        rows.append(
            {
                "numero": numero or "—",
                "student_id": student_id or "—",
                "student_name": student_name or "—",
                "course_name": course_name or "—",
                "grade_name": raw_grade or "—",
                "grade_label": _get_grade_display(raw_grade) or "—",
                "section_name": raw_section or "—",
                "section_label": _get_section_display(raw_section, inferred_cycle) or "—",
                "cycle_name": inferred_cycle or "—",
                "subject_code": subject_code or "—",
                "subject_name": str(entry.get("subject_name", "")).strip() or "—",
                "period_code": period_code or "—",
                "failed_blocks": failed_blocks,
                "failed_block_labels": [
                    str(block.get("block_label", "")).strip()
                    for block in failed_blocks
                    if str(block.get("block_label", "")).strip()
                ],
                "failed_blocks_count": int(entry.get("failed_blocks_count", 0)),
                "lowest_score": min(score_values) if score_values else None,
                "status": derived_status,
                "status_label": derived_status_label,
                "teacher_name": teacher_lookup.get((course_name, subject_code), ""),
            }
        )

    return sorted(
        rows,
        key=lambda item: (
            str(item.get("cycle_name", "")).strip(),
            _safe_int_for_sort(_extract_grade_number(item.get("grade_name", "")) or 999)[0],
            str(item.get("section_label", "")).strip(),
            _safe_int_for_sort(item.get("numero", "")),
            str(item.get("student_name", "")).strip(),
            str(item.get("subject_name", "")).strip(),
            str(item.get("period_code", "")).strip(),
        ),
    )


def _build_grouped_operational_rows(
    operational_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str], dict[str, Any]] = {}

    for row in operational_rows:
        key = (
            str(row.get("student_id", "")).strip(),
            str(row.get("course_name", "")).strip(),
            str(row.get("period_code", "")).strip(),
        )

        if key not in grouped:
            grouped[key] = {
                "numero": row.get("numero", "—"),
                "student_id": row.get("student_id", "—"),
                "student_name": row.get("student_name", "—"),
                "course_name": row.get("course_name", "—"),
                "grade_name": row.get("grade_name", "—"),
                "grade_label": row.get("grade_label", "—"),
                "section_name": row.get("section_name", "—"),
                "section_label": row.get("section_label", "—"),
                "cycle_name": row.get("cycle_name", "—"),
                "period_code": row.get("period_code", "—"),
                "status": row.get("status", "pendiente"),
                "status_label": row.get("status_label", "Pendiente"),
                "subjects": [],
            }

        current_status = grouped[key]["status"]
        new_status = row.get("status", "pendiente")

        if current_status != "no_recuperado" and new_status == "no_recuperado":
            grouped[key]["status"] = "no_recuperado"
            grouped[key]["status_label"] = "No recuperó"
        elif current_status not in {"no_recuperado", "en_riesgo"} and new_status == "en_riesgo":
            grouped[key]["status"] = "en_riesgo"
            grouped[key]["status_label"] = "Recuperación pedagógica"

        grouped[key]["subjects"].append(
            {
                "subject_code": row.get("subject_code", "—"),
                "subject_name": row.get("subject_name", "—"),
                "failed_block_labels": row.get("failed_block_labels", []),
                "failed_blocks": row.get("failed_blocks", []),
                "lowest_score": row.get("lowest_score"),
                "status": row.get("status", "pendiente"),
                "status_label": row.get("status_label", "Pendiente"),
            }
        )

    grouped_rows: list[dict[str, Any]] = []

    for payload in grouped.values():
        subject_map: dict[str, dict[str, Any]] = {}

        for subject in payload["subjects"]:
            subject_name = str(subject.get("subject_name", "")).strip() or "—"

            if subject_name not in subject_map:
                subject_map[subject_name] = {
                    "subject_code": subject.get("subject_code", "—"),
                    "subject_name": subject_name,
                    "failed_block_labels": [],
                    "failed_blocks": [],
                    "lowest_score": subject.get("lowest_score"),
                    "status": subject.get("status", "pendiente"),
                    "status_label": subject.get("status_label", "Pendiente"),
                }

            existing_labels = set(subject_map[subject_name]["failed_block_labels"])
            for label in subject.get("failed_block_labels", []):
                if label not in existing_labels:
                    subject_map[subject_name]["failed_block_labels"].append(label)
                    existing_labels.add(label)

            block_index: dict[str, dict[str, Any]] = {
                str(item.get("block_code", "")).strip() or str(item.get("block_label", "")).strip(): item
                for item in subject_map[subject_name]["failed_blocks"]
            }

            for block in subject.get("failed_blocks", []):
                block_key = str(block.get("block_code", "")).strip() or str(block.get("block_label", "")).strip()
                if not block_key:
                    continue

                block_label = str(block.get("block_label", "")).strip() or "Bloque"
                block_score = block.get("score")

                if block_key not in block_index:
                    block_index[block_key] = {
                        "block_code": str(block.get("block_code", "")).strip(),
                        "block_label": block_label,
                        "score": block_score,
                    }
                else:
                    current_score = block_index[block_key].get("score")
                    if current_score is None:
                        block_index[block_key]["score"] = block_score
                    elif block_score is not None:
                        block_index[block_key]["score"] = min(current_score, block_score)

                subject_map[subject_name]["failed_blocks"] = list(block_index.values())

            current_lowest = subject_map[subject_name]["lowest_score"]
            new_lowest = subject.get("lowest_score")
            if current_lowest is None:
                subject_map[subject_name]["lowest_score"] = new_lowest
            elif new_lowest is not None:
                subject_map[subject_name]["lowest_score"] = min(current_lowest, new_lowest)

            if (
                subject_map[subject_name]["status"] != "no_recuperado"
                and subject.get("status") == "no_recuperado"
            ):
                subject_map[subject_name]["status"] = "no_recuperado"
                subject_map[subject_name]["status_label"] = "No recuperó"

        for subject_payload in subject_map.values():
            subject_payload["failed_blocks"] = sorted(
                subject_payload["failed_blocks"],
                key=lambda item: (
                    str(item.get("block_label", "")).strip(),
                    str(item.get("block_code", "")).strip(),
                ),
            )

        payload["subjects"] = sorted(
            subject_map.values(),
            key=lambda item: str(item.get("subject_name", "")).strip(),
        )

        grouped_rows.append(payload)

    return sorted(
        grouped_rows,
        key=lambda item: (
            str(item.get("cycle_name", "")).strip(),
            _safe_int_for_sort(_extract_grade_number(item.get("grade_name", "")) or 999)[0],
            str(item.get("section_label", "")).strip(),
            _safe_int_for_sort(item.get("numero", "")),
            str(item.get("student_name", "")).strip(),
            str(item.get("period_code", "")).strip(),
        ),
    )


def build_tracking_dashboard_data(
    rows: list[dict[str, Any]],
    center_id: Optional[Any] = None,
    school_year: Optional[str] = None,
    ciclo: Optional[str] = None,
    course_name: Optional[str] = None,
    grade_name: Optional[str] = None,
    section_name: Optional[str] = None,
    period_code: Optional[str] = None,
    subject_code: Optional[str] = None,
    student_status: Optional[str] = None,
    student_id: Optional[str] = None,
    min_score: float = 70.0,
    teacher_assignments: Optional[list[dict[str, Any]]] = None,
) -> dict[str, Any]:
    raw_entries = build_risk_entries_from_rows(
        rows=rows,
        min_score=min_score,
    )

    filtered_entries = _apply_operational_filters(
        entries=raw_entries,
        ciclo=ciclo,
        course_name=course_name,
        grade_name=grade_name,
        section_name=section_name,
        period_code=period_code,
        subject_code=subject_code,
        student_id=student_id,
    )

    recovery_follow_up = _build_recovery_follow_up(filtered_entries)

    operational_rows = _build_operational_rows(
        entries=filtered_entries,
        recovery_follow_up=recovery_follow_up,
        teacher_assignments=teacher_assignments,
        student_status=student_status,
    )

    grouped_operational_rows = _build_grouped_operational_rows(operational_rows)

    detected_subjects = get_detected_academic_subjects(rows)
    catalog = _extract_grades_and_sections(raw_entries, selected_cycle=ciclo)

    students_affected = {
        (str(item.get("student_id", "")).strip(), str(item.get("course_name", "")).strip())
        for item in operational_rows
    }

    courses_with_cases = {
        str(item.get("course_name", "")).strip()
        for item in operational_rows
        if str(item.get("course_name", "")).strip() and str(item.get("course_name", "")).strip() != "—"
    }

    subjects_with_cases = {
        str(item.get("subject_name", "")).strip()
        for item in operational_rows
        if str(item.get("subject_name", "")).strip() and str(item.get("subject_name", "")).strip() != "—"
    }

    has_active_filters = any([
        _normalize_filter_value(ciclo),
        _normalize_filter_value(course_name),
        _normalize_filter_value(grade_name),
        _normalize_filter_value(section_name),
        _normalize_filter_value(period_code),
        _normalize_filter_value(subject_code),
        _normalize_filter_value(student_status),
        _normalize_filter_value(student_id),
    ])

    dashboard_data = {
        "filters": {
            "center_id": center_id,
            "school_year": school_year,
            "ciclo": ciclo,
            "curso": course_name,
            "grado": grade_name,
            "seccion": section_name,
            "periodo": period_code,
            "asignatura": subject_code,
            "estado": student_status,
            "student_id": student_id,
            "min_score": min_score,
        },
        "metadata": {
            "cycle_options": CYCLE_OPTIONS,
            "courses_detected": _extract_detected_courses(raw_entries),
            "grades_catalog": catalog["grades_catalog"],
            "sections_catalog": catalog["sections_catalog"],
            "sections_by_grade": catalog["sections_by_grade"],
            "periods_detected": get_supported_period_codes(),
            "subjects_catalog": detected_subjects,
            "entries_total": len(operational_rows),
            "has_active_filters": has_active_filters,
        },
        "summary": {
            "compact_cards": {
                "students_affected": len(students_affected),
                "courses_with_cases": len(courses_with_cases),
                "subjects_with_cases": len(subjects_with_cases),
            }
        },
        "operational_rows": operational_rows,
        "grouped_operational_rows": grouped_operational_rows,
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