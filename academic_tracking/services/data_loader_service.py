"""
data_loader_service.py

Capa de carga de datos para el módulo academic_tracking.

Objetivos:
- Desacoplar routes.py de la fuente real de datos
- Permitir conectar Google Sheets, BD o servicios internos sin tocar el dashboard
- Mantener compatibilidad con arquitectura multi-centro
- No tocar nada de boletines web o PDF

Importante:
- Este servicio está preparado para integrarse con la fuente actual del proyecto
- Las funciones de lectura real se pueden reemplazar sin afectar tracking_service
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import pandas as pd

from app.data.fetchers.google_sheets import (
    load_primer_ciclo,
    load_segundo_ciclo,
)


def normalize_row_keys(row: Dict[str, Any]) -> Dict[str, Any]:
    """
    Limpia llaves de una fila importada.
    """
    clean_row: Dict[str, Any] = {}

    for key, value in row.items():
        if key is None:
            continue
        clean_key = str(key).strip()
        clean_row[clean_key] = value

    return clean_row


def normalize_rows(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Limpia un conjunto de filas.
    """
    return [normalize_row_keys(row) for row in rows if isinstance(row, dict)]


def filter_rows_by_center(
    rows: List[Dict[str, Any]],
    center_id: Optional[Any] = None,
) -> List[Dict[str, Any]]:
    """
    Filtra por center_id cuando la fila lo contiene.

    Regla:
    - Si center_id no viene, devuelve todo
    - Si las filas no tienen center_id, no rompe; devuelve todo
    """
    if center_id in (None, "", "null"):
        return rows

    filtered: List[Dict[str, Any]] = []

    for row in rows:
        row_center_id = row.get("center_id")

        # Si la fuente todavía no incluye center_id por fila, no bloqueamos el módulo
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
    """
    Filtra asignaciones de docentes de manera flexible.
    """
    results: List[Dict[str, Any]] = []

    for row in teacher_rows:
        if center_id not in (None, "", "null"):
            if str(row.get("center_id", "")).strip() != str(center_id).strip():
                continue

        if school_year:
            if str(row.get("school_year", "")).strip() != str(school_year).strip():
                continue

        if ciclo:
            if str(row.get("ciclo", "")).strip() != str(ciclo).strip():
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
    """
    Punto único de carga de filas académicas.

    IMPORTANTE:
    Aquí se conecta la fuente actual real del proyecto.

    Fuente actual:
    - Primer ciclo: CSV remoto vía settings.url_primer_ciclo
    - Segundo ciclo: CSV remoto vía settings.url_segundo_ciclo

    Esta implementación:
    - reutiliza la misma fuente del sistema de boletines
    - unifica ambos ciclos en una sola lista de filas
    - queda lista para filtrar por centro cuando exista center_id en los datos
    """
    rows: List[Dict[str, Any]] = []

    try:
        df_primer = load_primer_ciclo()
        df_segundo = load_segundo_ciclo()

        if ciclo == "Primer_Ciclo":
            df = df_primer.copy()
        elif ciclo == "Segundo_Ciclo":
            df = df_segundo.copy()
        else:
            df = pd.concat([df_primer, df_segundo], ignore_index=True)

        rows = df.to_dict(orient="records")

    except Exception as exc:
        print(f"[academic_tracking] Error cargando filas académicas: {exc}")
        rows = []

    rows = normalize_rows(rows)
    rows = filter_rows_by_center(rows, center_id=center_id)

    return rows


def load_teacher_assignments_from_source(
    center_id: Optional[Any] = None,
    school_year: Optional[str] = None,
    ciclo: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Punto único de carga de docente_asignatura.

    Esta fuente debe ser auxiliar y separada de la tabla principal de notas.
    Puede venir de:
    - hoja Google Sheets auxiliar
    - tabla BD
    - configuración administrativa interna

    Por ahora devuelve vacío de forma segura hasta integrar la fuente real.
    """
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