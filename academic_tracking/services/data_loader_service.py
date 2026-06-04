"""
data_loader_service.py

Capa de carga de datos para el módulo academic_tracking.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import pandas as pd

from app.data.fetchers.google_sheets import (
    load_control_asistencia_completivo_primer_ciclo,
    load_control_asistencia_completivo_segundo_ciclo,
    load_primer_ciclo,
    load_segundo_ciclo,
)


def normalize_cycle_key(ciclo: Optional[str] = None) -> Optional[str]:
    if ciclo is None:
        return None

    text = str(ciclo).strip().lower()
    text = text.replace("_", " ")
    text = " ".join(text.split())

    if text in {"primer ciclo", "primer"}:
        return "Primer Ciclo"

    if text in {"segundo ciclo", "segundo"}:
        return "Segundo Ciclo"

    return None


def normalize_row_keys(row: Dict[str, Any]) -> Dict[str, Any]:
    clean_row: Dict[str, Any] = {}

    for key, value in row.items():
        if key is None:
            continue

        clean_key = str(key).strip()
        clean_row[clean_key] = value

    return clean_row


def normalize_rows(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [normalize_row_keys(row) for row in rows if isinstance(row, dict)]


def filter_rows_by_center(
    rows: List[Dict[str, Any]],
    center_id: Optional[Any] = None,
) -> List[Dict[str, Any]]:
    if center_id in (None, "", "null"):
        return rows

    filtered: List[Dict[str, Any]] = []

    for row in rows:
        row_center_id = row.get("center_id")

        if row_center_id is None:
            filtered.append(row)
            continue

        if str(row_center_id).strip() == str(center_id).strip():
            filtered.append(row)

    return filtered


def filter_teacher_assignments(
    teacher_rows: List[Dict[str, Any]],
    center_id: Optional[Any] = None,
    school_year: Optional[str] = None,
    ciclo: Optional[str] = None,
    curso: Optional[str] = None,
    asignatura_codigo: Optional[str] = None,
) -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []
    normalized_cycle = normalize_cycle_key(ciclo)

    for row in teacher_rows:
        if center_id not in (None, "", "null"):
            if str(row.get("center_id", "")).strip() != str(center_id).strip():
                continue

        if school_year:
            if str(row.get("school_year", "")).strip() != str(school_year).strip():
                continue

        if normalized_cycle:
            row_cycle = normalize_cycle_key(row.get("ciclo"))
            if row_cycle != normalized_cycle:
                continue

        if curso:
            if str(row.get("curso", "")).strip() != str(curso).strip():
                continue

        if asignatura_codigo:
            if str(row.get("asignatura_codigo", "")).strip() != str(asignatura_codigo).strip():
                continue

        activo = row.get("activo", True)

        if str(activo).strip().lower() in {"false", "0", "no", "inactive", "inactivo"}:
            continue

        results.append(row)

    return results


def load_academic_rows_from_source(
    center_id: Optional[Any] = None,
    school_year: Optional[str] = None,
    ciclo: Optional[str] = None,
) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []

    try:
        normalized_cycle = normalize_cycle_key(ciclo)

        if normalized_cycle == "Primer Ciclo":
            df = load_primer_ciclo().copy()

        elif normalized_cycle == "Segundo Ciclo":
            df = load_segundo_ciclo().copy()

        else:
            df_primer = load_primer_ciclo()
            df_segundo = load_segundo_ciclo()
            df = pd.concat([df_primer, df_segundo], ignore_index=True)

        rows = df.to_dict(orient="records")

    except Exception as exc:
        print(f"[academic_tracking] Error cargando filas académicas: {exc}")
        rows = []

    rows = normalize_rows(rows)
    rows = filter_rows_by_center(rows, center_id=center_id)

    return rows


def load_completivo_attendance_control_rows_from_source(
    center_id: Optional[Any] = None,
    school_year: Optional[str] = None,
    ciclo: Optional[str] = None,
) -> Dict[str, List[Dict[str, Any]]]:
    normalized_cycle = normalize_cycle_key(ciclo)

    primer_rows: List[Dict[str, Any]] = []
    segundo_rows: List[Dict[str, Any]] = []

    if normalized_cycle in (None, "Primer Ciclo"):
        try:
            df_primer = load_control_asistencia_completivo_primer_ciclo()
            primer_rows = df_primer.to_dict(orient="records")
        except Exception as exc:
            print(
                "[academic_tracking] Error cargando control de asistencia "
                f"completivo primer ciclo: {exc}"
            )
            primer_rows = []

    if normalized_cycle in (None, "Segundo Ciclo"):
        try:
            df_segundo = load_control_asistencia_completivo_segundo_ciclo()
            segundo_rows = df_segundo.to_dict(orient="records")
        except Exception as exc:
            print(
                "[academic_tracking] Error cargando control de asistencia "
                f"completivo segundo ciclo: {exc}"
            )
            segundo_rows = []

    primer_rows = normalize_rows(primer_rows)
    segundo_rows = normalize_rows(segundo_rows)

    primer_rows = filter_rows_by_center(primer_rows, center_id=center_id)
    segundo_rows = filter_rows_by_center(segundo_rows, center_id=center_id)

    return {
        "primer_ciclo": primer_rows,
        "segundo_ciclo": segundo_rows,
    }


def load_teacher_assignments_from_source(
    center_id: Optional[Any] = None,
    school_year: Optional[str] = None,
    ciclo: Optional[str] = None,
) -> List[Dict[str, Any]]:
    teacher_rows: List[Dict[str, Any]] = []

    try:
        teacher_rows = []
    except Exception as exc:
        print(f"[academic_tracking] Error cargando docente_asignatura: {exc}")
        teacher_rows = []

    teacher_rows = normalize_rows(teacher_rows)
    teacher_rows = filter_teacher_assignments(
        teacher_rows=teacher_rows,
        center_id=center_id,
        school_year=school_year,
        ciclo=ciclo,
    )

    return teacher_rows