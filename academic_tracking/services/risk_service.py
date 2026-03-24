"""
risk_service.py

Servicio de análisis de riesgo académico para el módulo academic_tracking.

Responsabilidades:
- Evaluar el estado de un período por asignatura
- Detectar bloques reprobados dentro del período
- Identificar períodos comprometidos por estudiante/asignatura
- Preparar estructuras listas para el dashboard de seguimiento

Estados manejados:
- passed: todos los bloques reportados y >= nota mínima
- compromised: todos los bloques reportados, pero uno o más < nota mínima
- incomplete: falta uno o más bloques del período
"""

from __future__ import annotations

from typing import Any, Optional

from .parsing_service import (
    DEFAULT_MIN_COMPETENCY_SCORE,
    get_supported_block_codes,
    parse_student_row,
)


PERIOD_STATUS_PASSED = "passed"
PERIOD_STATUS_COMPROMISED = "compromised"
PERIOD_STATUS_INCOMPLETE = "incomplete"

PERIOD_STATUS_LABELS = {
    PERIOD_STATUS_PASSED: "Superado",
    PERIOD_STATUS_COMPROMISED: "Comprometido",
    PERIOD_STATUS_INCOMPLETE: "Incompleto",
}


def is_failed_competency(
    value: Optional[float],
    min_score: float = DEFAULT_MIN_COMPETENCY_SCORE,
) -> bool:
    """
    Indica si una calificación de bloque está por debajo del mínimo aprobatorio.
    """
    if value is None:
        return False
    return float(value) < float(min_score)


def is_missing_score(value: Optional[float]) -> bool:
    """
    Indica si un bloque no tiene calificación reportada.
    """
    return value is None


def build_failed_block_payload(
    block_code: str,
    block_data: dict[str, Any],
) -> dict[str, Any]:
    """
    Construye la representación estándar de un bloque reprobado.
    """
    return {
        "block_code": block_code,
        "block_label": block_data.get("block_label", block_code),
        "score": block_data.get("score"),
        "column_name": block_data.get("column_name", ""),
    }


def evaluate_period_blocks(
    blocks: dict[str, dict[str, Any]],
    min_score: float = DEFAULT_MIN_COMPETENCY_SCORE,
) -> dict[str, Any]:
    """
    Evalúa los 4 bloques de un período y determina su estado.

    Reglas:
    - incomplete: falta uno o más bloques o tienen score None
    - compromised: todos los bloques reportados, pero uno o más < min_score
    - passed: todos los bloques reportados y todos >= min_score
    """
    expected_block_codes = get_supported_block_codes()

    reported_blocks: list[dict[str, Any]] = []
    missing_block_codes: list[str] = []
    failed_blocks: list[dict[str, Any]] = []

    for block_code in expected_block_codes:
        block_data = blocks.get(block_code)

        if not block_data:
            missing_block_codes.append(block_code)
            continue

        score = block_data.get("score")

        if is_missing_score(score):
            missing_block_codes.append(block_code)
            continue

        reported_blocks.append(
            {
                "block_code": block_code,
                "block_label": block_data.get("block_label", block_code),
                "score": score,
                "column_name": block_data.get("column_name", ""),
            }
        )

        if is_failed_competency(score, min_score=min_score):
            failed_blocks.append(build_failed_block_payload(block_code, block_data))

    reported_blocks_count = len(reported_blocks)
    missing_blocks_count = len(missing_block_codes)
    failed_blocks_count = len(failed_blocks)

    all_blocks_reported = missing_blocks_count == 0

    if not all_blocks_reported:
        period_status = PERIOD_STATUS_INCOMPLETE
    elif failed_blocks_count > 0:
        period_status = PERIOD_STATUS_COMPROMISED
    else:
        period_status = PERIOD_STATUS_PASSED

    return {
        "period_status": period_status,
        "period_status_label": PERIOD_STATUS_LABELS[period_status],
        "all_blocks_reported": all_blocks_reported,
        "reported_blocks_count": reported_blocks_count,
        "missing_blocks_count": missing_blocks_count,
        "missing_block_codes": missing_block_codes,
        "failed_blocks_count": failed_blocks_count,
        "failed_blocks": failed_blocks,
        "reported_blocks": reported_blocks,
    }


def build_student_subject_period_statuses(
    parsed_row: dict[str, Any],
    min_score: float = DEFAULT_MIN_COMPETENCY_SCORE,
) -> list[dict[str, Any]]:
    """
    Construye una lista de estados por estudiante + asignatura + período.

    Entrada:
    - parsed_row: salida de parse_student_row()

    Salida:
    [
        {
            "student_id": "...",
            "student_name": "...",
            "numero": "...",
            "curso": "...",
            "prof_titular": "...",
            "subject_code": "MAT",
            "subject_name": "Matemática",
            "period_code": "P2",
            "period_status": "compromised",
            ...
        }
    ]
    """
    student = parsed_row.get("student", {})
    subjects = parsed_row.get("subjects", {})

    student_id = student.get("id_estudiante", "")
    student_name = student.get("nombre_estudiante", "")
    numero = student.get("numero", "")
    curso = student.get("curso", "")
    prof_titular = student.get("prof_titular", "")

    results: list[dict[str, Any]] = []

    for subject_code, subject_payload in subjects.items():
        subject_name = subject_payload.get("subject_name", subject_code)
        periods = subject_payload.get("periods", {})

        for period_code, period_payload in periods.items():
            blocks = period_payload.get("blocks", {})

            period_evaluation = evaluate_period_blocks(
                blocks=blocks,
                min_score=min_score,
            )

            results.append(
                {
                    "student_id": student_id,
                    "student_name": student_name,
                    "numero": numero,
                    "curso": curso,
                    "prof_titular": prof_titular,
                    "subject_code": subject_code,
                    "subject_name": subject_name,
                    "period_code": period_code,
                    "period_status": period_evaluation["period_status"],
                    "period_status_label": period_evaluation["period_status_label"],
                    "all_blocks_reported": period_evaluation["all_blocks_reported"],
                    "reported_blocks_count": period_evaluation["reported_blocks_count"],
                    "missing_blocks_count": period_evaluation["missing_blocks_count"],
                    "missing_block_codes": period_evaluation["missing_block_codes"],
                    "failed_blocks_count": period_evaluation["failed_blocks_count"],
                    "failed_blocks": period_evaluation["failed_blocks"],
                    "reported_blocks": period_evaluation["reported_blocks"],
                }
            )

    return results


def build_risk_entries_from_row(
    row: dict[str, Any],
    min_score: float = DEFAULT_MIN_COMPETENCY_SCORE,
) -> list[dict[str, Any]]:
    """
    Parsea una fila cruda y devuelve sus estados por asignatura/período.
    """
    parsed_row = parse_student_row(row)
    return build_student_subject_period_statuses(
        parsed_row=parsed_row,
        min_score=min_score,
    )


def build_risk_entries_from_rows(
    rows: list[dict[str, Any]],
    min_score: float = DEFAULT_MIN_COMPETENCY_SCORE,
) -> list[dict[str, Any]]:
    """
    Procesa múltiples filas crudas y devuelve una lista consolidada de
    estados por estudiante/asignatura/período.
    """
    all_entries: list[dict[str, Any]] = []

    for row in rows:
        if not isinstance(row, dict):
            continue

        row_entries = build_risk_entries_from_row(
            row=row,
            min_score=min_score,
        )

        all_entries.extend(row_entries)

    return all_entries


def filter_period_status_entries(
    entries: list[dict[str, Any]],
    period_status: str,
) -> list[dict[str, Any]]:
    """
    Filtra entradas por estado del período.
    """
    return [
        entry
        for entry in entries
        if entry.get("period_status") == period_status
    ]


def get_compromised_entries(
    entries: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Retorna entradas cuyo período quedó comprometido.
    """
    return filter_period_status_entries(entries, PERIOD_STATUS_COMPROMISED)


def get_incomplete_entries(
    entries: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Retorna entradas con reporte incompleto.
    """
    return filter_period_status_entries(entries, PERIOD_STATUS_INCOMPLETE)


def get_passed_entries(
    entries: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Retorna entradas con período superado.
    """
    return filter_period_status_entries(entries, PERIOD_STATUS_PASSED)


def count_period_statuses(
    entries: list[dict[str, Any]],
) -> dict[str, int]:
    """
    Cuenta cuántas entradas hay por estado.
    """
    return {
        PERIOD_STATUS_PASSED: len(get_passed_entries(entries)),
        PERIOD_STATUS_COMPROMISED: len(get_compromised_entries(entries)),
        PERIOD_STATUS_INCOMPLETE: len(get_incomplete_entries(entries)),
    }


def get_student_compromised_periods(
    entries: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Retorna solo los períodos comprometidos, con la información esencial
    para el dashboard o listas de seguimiento.
    """
    compromised_entries = get_compromised_entries(entries)

    return [
        {
            "student_id": entry.get("student_id", ""),
            "student_name": entry.get("student_name", ""),
            "numero": entry.get("numero", ""),
            "curso": entry.get("curso", ""),
            "subject_code": entry.get("subject_code", ""),
            "subject_name": entry.get("subject_name", ""),
            "period_code": entry.get("period_code", ""),
            "failed_blocks_count": entry.get("failed_blocks_count", 0),
            "failed_blocks": entry.get("failed_blocks", []),
        }
        for entry in compromised_entries
    ]