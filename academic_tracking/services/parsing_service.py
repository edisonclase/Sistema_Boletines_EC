"""
parsing_service.py

Servicio base para interpretar la estructura académica importada desde Google Sheets
sin alterar la fuente original.

Objetivo:
- Detectar asignaturas a partir de los prefijos de columnas
- Detectar períodos disponibles (P1, P2, P3, P4)
- Agrupar columnas de competencias por asignatura y período
- Normalizar valores provenientes del sheet
- Preparar estructuras limpias para status_service, risk_service y tracking_service

Reglas de diseño:
- No depende de PDF ni boletines
- No asume una sola institución
- No rompe la estructura actual del import
"""

from __future__ import annotations

import math
import re
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

# Catálogo oficial de asignaturas para este módulo.
# Debe coincidir con los prefijos reales de la hoja principal.
SUBJECTS: Dict[str, str] = {
    "LEN": "Lengua Española",
    "ING": "Inglés",
    "FRA": "Francés",
    "MAT": "Matemática",
    "SOC": "Ciencias Sociales",
    "NAT": "Ciencias de la Naturaleza",
    "ART": "Educación Artística",
    "FIS": "Educación Física",
    "FOR": "Formación Humana",
}

PERIODS: Tuple[str, ...] = ("P1", "P2", "P3", "P4")
COMPETENCY_KEYS: Tuple[str, ...] = ("C1", "C2", "C3", "C4")

# Campos base frecuentes de la hoja principal
BASE_FIELDS: Tuple[str, ...] = (
    "ID_ESTUDIANTE",
    "NOMBRE_ESTUDIANTE",
    "NUMERO",
    "CURSO",
    "PROF_TITULAR",
    "ASIST_ANUAL_PCT",
    "SITUACION_PROMOVIDO",
    "SITUACION_REPITENTE",
    "COMENTARIO_FINAL",
)

# Regex para detectar columnas tipo LEN_C1_P1, MAT_C4_P3, etc.
COMPETENCY_COLUMN_PATTERN = re.compile(
    r"^(?P<subject>[A-Z]{3})_(?P<competency>C[1-4])_(?P<period>P[1-4])$"
)

# Regex para detectar otros campos de asignatura, por si luego se necesitan
SUBJECT_GENERIC_COLUMN_PATTERN = re.compile(r"^(?P<subject>[A-Z]{3})_(?P<suffix>.+)$")


def normalize_text(value: Any) -> str:
    """
    Convierte cualquier valor a texto limpio.
    """
    if value is None:
        return ""

    text = str(value).strip()

    # Normalizar textos "vacíos" comunes en imports
    if text.lower() in {"nan", "none", "null"}:
        return ""

    return text


def normalize_numeric(value: Any) -> Optional[float]:
    """
    Convierte un valor a float si es posible.
    Devuelve None si el valor está vacío o no es numérico.
    """
    if value is None:
        return None

    if isinstance(value, bool):
        return None

    if isinstance(value, (int, float)):
        if isinstance(value, float) and math.isnan(value):
            return None
        return float(value)

    text = normalize_text(value)
    if not text:
        return None

    # Permitir coma decimal si viene de hojas o CSV exportado
    text = text.replace(",", ".")

    try:
        return float(text)
    except ValueError:
        return None


def is_value_present(value: Any) -> bool:
    """
    Determina si un valor se considera presente para fines de reporte.
    """
    if value is None:
        return False

    if isinstance(value, str):
        return normalize_text(value) != ""

    if isinstance(value, float):
        return not math.isnan(value)

    return True


def normalize_course_name(course: Any) -> str:
    """
    Normaliza el nombre del curso para comparaciones seguras.
    Mantiene el contenido humano, pero limpia espacios.
    """
    return re.sub(r"\s+", " ", normalize_text(course))


def safe_bool(value: Any) -> bool:
    """
    Interpreta valores comunes de booleanos.
    """
    if isinstance(value, bool):
        return value

    text = normalize_text(value).lower()
    return text in {"1", "true", "t", "yes", "y", "si", "sí", "activo"}


def get_row_value(row: Dict[str, Any], key: str, default: Any = None) -> Any:
    """
    Obtiene una clave desde una fila sin romper si no existe.
    """
    return row.get(key, default)


def get_student_base_info(row: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extrae los campos base mínimos de un estudiante.
    """
    return {
        "id_estudiante": normalize_text(get_row_value(row, "ID_ESTUDIANTE")),
        "nombre_estudiante": normalize_text(get_row_value(row, "NOMBRE_ESTUDIANTE")),
        "numero": normalize_text(get_row_value(row, "NUMERO")),
        "curso": normalize_course_name(get_row_value(row, "CURSO")),
        "prof_titular": normalize_text(get_row_value(row, "PROF_TITULAR")),
    }


def detect_subjects_from_columns(columns: Iterable[str]) -> List[str]:
    """
    Detecta asignaturas reales presentes en el dataset
    basándose en columnas tipo XXX_C1_P1.
    """
    found: Set[str] = set()

    for column in columns:
        match = COMPETENCY_COLUMN_PATTERN.match(column)
        if not match:
            continue

        subject_code = match.group("subject")
        if subject_code in SUBJECTS:
            found.add(subject_code)

    return sorted(found)


def detect_periods_from_columns(columns: Iterable[str]) -> List[str]:
    """
    Detecta períodos reales presentes en el dataset.
    """
    found: Set[str] = set()

    for column in columns:
        match = COMPETENCY_COLUMN_PATTERN.match(column)
        if not match:
            continue

        period = match.group("period")
        if period in PERIODS:
            found.add(period)

    return [period for period in PERIODS if period in found]


def build_subject_period_competency_columns(
    columns: Iterable[str],
) -> Dict[str, Dict[str, List[str]]]:
    """
    Construye un índice de columnas por asignatura y período.

    Salida esperada:
    {
        "LEN": {
            "P1": ["LEN_C1_P1", "LEN_C2_P1", "LEN_C3_P1", "LEN_C4_P1"],
            "P2": [...],
        },
        ...
    }
    """
    grouped: Dict[str, Dict[str, List[str]]] = {
        subject_code: {period: [] for period in PERIODS} for subject_code in SUBJECTS
    }

    for column in columns:
        match = COMPETENCY_COLUMN_PATTERN.match(column)
        if not match:
            continue

        subject_code = match.group("subject")
        competency_code = match.group("competency")
        period_code = match.group("period")

        if subject_code not in SUBJECTS or period_code not in PERIODS:
            continue

        grouped[subject_code][period_code].append(column)

    # Ordenar siempre por C1, C2, C3, C4
    for subject_code in grouped:
        for period_code in grouped[subject_code]:
            grouped[subject_code][period_code].sort(
                key=lambda col: COMPETENCY_KEYS.index(col.split("_")[1])
                if len(col.split("_")) >= 3 and col.split("_")[1] in COMPETENCY_KEYS
                else 999
            )

    # Eliminar asignaturas completamente vacías del índice
    clean_grouped: Dict[str, Dict[str, List[str]]] = {}
    for subject_code, periods_map in grouped.items():
        has_any_column = any(periods_map[period] for period in PERIODS)
        if has_any_column:
            clean_grouped[subject_code] = periods_map

    return clean_grouped


def build_subject_column_index(columns: Iterable[str]) -> Dict[str, List[str]]:
    """
    Índice general de columnas por asignatura.
    Útil para futuras etapas del módulo.
    """
    grouped: Dict[str, List[str]] = {}

    for column in columns:
        match = SUBJECT_GENERIC_COLUMN_PATTERN.match(column)
        if not match:
            continue

        subject_code = match.group("subject")
        if subject_code not in SUBJECTS:
            continue

        grouped.setdefault(subject_code, []).append(column)

    for subject_code in grouped:
        grouped[subject_code].sort()

    return grouped


def get_competency_columns_for_subject_period(
    subject_code: str,
    period_code: str,
    subject_period_map: Dict[str, Dict[str, List[str]]],
) -> List[str]:
    """
    Devuelve las columnas de competencias para una asignatura y período.
    """
    return subject_period_map.get(subject_code, {}).get(period_code, [])


def extract_competency_values_from_row(
    row: Dict[str, Any],
    subject_code: str,
    period_code: str,
    subject_period_map: Dict[str, Dict[str, List[str]]],
) -> Dict[str, Optional[float]]:
    """
    Extrae los valores numéricos de competencias de una fila para una asignatura y período.

    Salida esperada:
    {
        "C1": 85.0,
        "C2": 72.0,
        "C3": None,
        "C4": 90.0
    }
    """
    competency_columns = get_competency_columns_for_subject_period(
        subject_code=subject_code,
        period_code=period_code,
        subject_period_map=subject_period_map,
    )

    values: Dict[str, Optional[float]] = {}

    for column in competency_columns:
        parts = column.split("_")
        if len(parts) != 3:
            continue

        competency_code = parts[1]
        raw_value = get_row_value(row, column)
        values[competency_code] = normalize_numeric(raw_value)

    # Garantizar estructura completa aunque falten columnas
    for competency_code in COMPETENCY_KEYS:
        values.setdefault(competency_code, None)

    return values


def row_has_any_reported_value_for_subject_period(
    row: Dict[str, Any],
    subject_code: str,
    period_code: str,
    subject_period_map: Dict[str, Dict[str, List[str]]],
) -> bool:
    """
    Indica si una fila tiene al menos una calificación reportada
    para una asignatura y período.
    """
    competency_columns = get_competency_columns_for_subject_period(
        subject_code=subject_code,
        period_code=period_code,
        subject_period_map=subject_period_map,
    )

    for column in competency_columns:
        if is_value_present(get_row_value(row, column)):
            return True

    return False


def row_count_reported_competencies_for_subject_period(
    row: Dict[str, Any],
    subject_code: str,
    period_code: str,
    subject_period_map: Dict[str, Dict[str, List[str]]],
) -> int:
    """
    Cuenta cuántas competencias tienen valor reportado
    en una fila para una asignatura y período.
    """
    competency_columns = get_competency_columns_for_subject_period(
        subject_code=subject_code,
        period_code=period_code,
        subject_period_map=subject_period_map,
    )

    return sum(
        1 for column in competency_columns if is_value_present(get_row_value(row, column))
    )


def filter_rows_by_course(rows: Iterable[Dict[str, Any]], course_name: str) -> List[Dict[str, Any]]:
    """
    Filtra filas por curso.
    """
    normalized_target = normalize_course_name(course_name)
    return [
        row
        for row in rows
        if normalize_course_name(get_row_value(row, "CURSO")) == normalized_target
    ]


def get_available_courses(rows: Iterable[Dict[str, Any]]) -> List[str]:
    """
    Devuelve la lista de cursos únicos presentes en las filas.
    """
    courses = {
        normalize_course_name(get_row_value(row, "CURSO"))
        for row in rows
        if normalize_course_name(get_row_value(row, "CURSO"))
    }
    return sorted(courses)


def build_dataset_metadata(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Construye metadatos del dataset para uso interno del módulo.
    """
    columns: List[str] = list(rows[0].keys()) if rows else []
    detected_subjects = detect_subjects_from_columns(columns)
    detected_periods = detect_periods_from_columns(columns)
    subject_period_map = build_subject_period_competency_columns(columns)
    subject_column_index = build_subject_column_index(columns)

    return {
        "row_count": len(rows),
        "columns": columns,
        "base_fields": list(BASE_FIELDS),
        "subjects_detected": detected_subjects,
        "periods_detected": detected_periods,
        "courses_detected": get_available_courses(rows),
        "subject_period_map": subject_period_map,
        "subject_column_index": subject_column_index,
    }


def build_student_period_snapshot(
    row: Dict[str, Any],
    subject_period_map: Dict[str, Dict[str, List[str]]],
    subjects: Optional[List[str]] = None,
    periods: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Construye una vista resumida de una fila para análisis posteriores.

    Salida:
    {
        "student": {...},
        "subjects": {
            "LEN": {
                "P1": {"C1": 80.0, "C2": None, ...},
                "P2": {...}
            }
        }
    }
    """
    selected_subjects = subjects or list(subject_period_map.keys())
    selected_periods = periods or list(PERIODS)

    snapshot = {
        "student": get_student_base_info(row),
        "subjects": {},
    }

    for subject_code in selected_subjects:
        if subject_code not in subject_period_map:
            continue

        snapshot["subjects"][subject_code] = {}

        for period_code in selected_periods:
            if period_code not in PERIODS:
                continue

            snapshot["subjects"][subject_code][period_code] = extract_competency_values_from_row(
                row=row,
                subject_code=subject_code,
                period_code=period_code,
                subject_period_map=subject_period_map,
            )

    return snapshot


def build_rows_snapshots(
    rows: List[Dict[str, Any]],
    subject_period_map: Dict[str, Dict[str, List[str]]],
    subjects: Optional[List[str]] = None,
    periods: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """
    Construye snapshots de múltiples filas.
    """
    return [
        build_student_period_snapshot(
            row=row,
            subject_period_map=subject_period_map,
            subjects=subjects,
            periods=periods,
        )
        for row in rows
    ]


def parse_academic_rows(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Punto de entrada principal del servicio.

    Recibe filas crudas del sheet y devuelve una estructura base
    lista para que otros servicios la usen.

    Salida esperada:
    {
        "metadata": {...},
        "rows": [...],
        "snapshots": [...]
    }
    """
    metadata = build_dataset_metadata(rows)
    subject_period_map = metadata["subject_period_map"]

    return {
        "metadata": metadata,
        "rows": rows,
        "snapshots": build_rows_snapshots(
            rows=rows,
            subject_period_map=subject_period_map,
            subjects=metadata["subjects_detected"],
            periods=metadata["periods_detected"],
        ),
    }