"""
parsing_service.py

Servicio de parsing para el módulo academic_tracking.

Responsabilidades:
- Normalizar identificadores provenientes de Google Sheets / CSV
- Detectar columnas académicas válidas por patrón
- Excluir módulos formativos y columnas no relevantes para seguimiento
- Convertir una fila cruda del sheet en una estructura académica usable
- Preparar la base para evaluación por:
    estudiante + asignatura + período + bloque

Importante:
- Este módulo trabaja SOLO con asignaturas académicas
- No procesa módulos formativos (MOD1, MOD2, etc.)
- No usa todavía promedios finales ni lógica de cierre anual
"""

from __future__ import annotations

import re
import unicodedata
from typing import Any, Optional


DEFAULT_MIN_COMPETENCY_SCORE = 70.0

COMPETENCY_BLOCK_LABELS = {
    "C1": "Competencia Comunicativa",
    "C2": "Pensamiento Lógico, Creativo y Crítico",
    "C3": "Científica y Tecnológica / Ambiental y de la Salud / Desarrollo Personal y Espiritual",
    "C4": "Ética y Ciudadana",
}

SUBJECT_LABELS = {
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

NON_ACADEMIC_PREFIXES = {
    "MOD1",
    "MOD2",
    "MOD3",
    "MOD4",
    "MOD5",
}

ACADEMIC_BLOCK_COLUMN_PATTERN = re.compile(
    r"^(?P<subject>[A-Z0-9]+)_(?P<block>C[1-4])_(?P<period>P[1-4])$"
)

VALID_PERIOD_CODES = {"P1", "P2", "P3", "P4"}
VALID_BLOCK_CODES = {"C1", "C2", "C3", "C4"}

IDENTITY_COLUMN_CANDIDATES = {
    "id_estudiante": [
        "ID_ESTUDIANTE",
        "ID ESTUDIANTE",
        "ID",
        "MATRICULA",
        "MATRÍCULA",
        "CODIGO",
        "CÓDIGO",
        "CODIGO_ESTUDIANTE",
        "CODIGO DEL ESTUDIANTE",
    ],
    "nombre_estudiante": [
        "NOMBRE_ESTUDIANTE",
        "NOMBRE ESTUDIANTE",
        "NOMBRE",
        "ESTUDIANTE",
        "NOMBRE_COMPLETO",
        "NOMBRE COMPLETO",
        "APELLIDOS Y NOMBRES",
        "NOMBRES Y APELLIDOS",
    ],
    "numero": [
        "NUMERO",
        "NÚMERO",
        "NO",
        "NO.",
        "N0",
        "#",
        "NUM",
        "NUM.",
        "NUM_LISTA",
        "NUMERO_LISTA",
        "NÚMERO_LISTA",
        "LISTA",
        "NO_LISTA",
    ],
    "curso": [
        "CURSO",
        "GRADO",
        "SECCION",
        "SECCIÓN",
        "CURSO_SECCION",
        "CURSO_SECCIÓN",
        "CURSO / SECCION",
        "CURSO / SECCIÓN",
        "GRADO_SECCION",
        "GRADO_SECCIÓN",
    ],
    "prof_titular": [
        "PROF_TITULAR",
        "PROF TITULAR",
        "PROFESOR_TITULAR",
        "PROFESOR TITULAR",
        "DOCENTE_TITULAR",
        "DOCENTE TITULAR",
        "TITULAR",
        "MAESTRO_TITULAR",
        "MAESTRO TITULAR",
    ],
}


def normalize_sheet_identifier(value: Any) -> str:
    """
    Normaliza identificadores que pueden venir como float desde pandas/CSV.

    Ejemplos:
    - 12345.0 -> "12345"
    - "00123.0" -> "00123"
    - None -> ""
    - nan -> ""
    """
    if value is None:
        return ""

    text = str(value).strip()

    if not text:
        return ""

    if text.lower() == "nan":
        return ""

    if text.endswith(".0"):
        text = text[:-2]

    return text


def normalize_text(value: Any) -> str:
    """
    Normaliza texto general.
    """
    if value is None:
        return ""

    text = str(value).strip()

    if not text or text.lower() == "nan":
        return ""

    return text


def normalize_header_key(value: Any) -> str:
    """
    Normaliza encabezados para comparación flexible:
    - quita tildes
    - pasa a mayúsculas
    - reemplaza espacios, puntos, guiones y slash por underscore
    - colapsa underscores repetidos
    """
    text = normalize_text(value)
    if not text:
        return ""

    text = unicodedata.normalize("NFD", text)
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    text = text.upper().strip()

    text = re.sub(r"[\s\./\\\-]+", "_", text)
    text = re.sub(r"_+", "_", text).strip("_")

    return text


def safe_float(value: Any) -> Optional[float]:
    """
    Convierte un valor a float de forma segura.

    Retorna None si:
    - está vacío
    - es NaN
    - no puede convertirse
    """
    if value is None:
        return None

    if isinstance(value, (int, float)):
        text = str(value).strip()
        if text.lower() == "nan":
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    text = str(value).strip()

    if not text or text.lower() == "nan":
        return None

    text = text.replace(",", ".")

    try:
        return float(text)
    except ValueError:
        return None


def get_subject_name(subject_code: str) -> str:
    subject_code = normalize_text(subject_code).upper()
    return SUBJECT_LABELS.get(subject_code, subject_code)


def get_competency_block_label(block_code: str) -> str:
    block_code = normalize_text(block_code).upper()
    return COMPETENCY_BLOCK_LABELS.get(block_code, block_code)


def is_non_academic_prefix(subject_code: str) -> bool:
    subject_code = normalize_text(subject_code).upper()
    return subject_code in NON_ACADEMIC_PREFIXES


def is_supported_academic_subject(subject_code: str) -> bool:
    subject_code = normalize_text(subject_code).upper()

    if not subject_code:
        return False

    if is_non_academic_prefix(subject_code):
        return False

    return subject_code in SUBJECT_LABELS


def is_academic_block_column(column_name: str) -> bool:
    if not column_name:
        return False

    normalized = normalize_header_key(column_name)

    match = ACADEMIC_BLOCK_COLUMN_PATTERN.match(normalized)
    if not match:
        return False

    subject_code = match.group("subject").upper()
    block_code = match.group("block").upper()
    period_code = match.group("period").upper()

    if subject_code in NON_ACADEMIC_PREFIXES:
        return False

    if subject_code not in SUBJECT_LABELS:
        return False

    if block_code not in VALID_BLOCK_CODES:
        return False

    if period_code not in VALID_PERIOD_CODES:
        return False

    return True


def parse_academic_block_column(column_name: str) -> Optional[dict[str, str]]:
    """
    Parsea una columna académica válida y devuelve sus partes.
    """
    if not column_name:
        return None

    normalized = normalize_header_key(column_name)
    match = ACADEMIC_BLOCK_COLUMN_PATTERN.match(normalized)

    if not match:
        return None

    subject_code = match.group("subject").upper()
    block_code = match.group("block").upper()
    period_code = match.group("period").upper()

    if not is_supported_academic_subject(subject_code):
        return None

    return {
        "column_name": normalized,
        "subject_code": subject_code,
        "subject_name": get_subject_name(subject_code),
        "block_code": block_code,
        "block_label": get_competency_block_label(block_code),
        "period_code": period_code,
    }


def _build_normalized_row_lookup(row: dict[str, Any]) -> dict[str, Any]:
    """
    Crea un índice flexible por encabezado normalizado.
    """
    normalized_lookup: dict[str, Any] = {}

    for raw_key, raw_value in row.items():
        normalized_key = normalize_header_key(raw_key)
        if normalized_key and normalized_key not in normalized_lookup:
            normalized_lookup[normalized_key] = raw_value

    return normalized_lookup


def _get_first_matching_value(
    normalized_row: dict[str, Any],
    candidates: list[str],
) -> Any:
    for candidate in candidates:
        normalized_candidate = normalize_header_key(candidate)
        if normalized_candidate in normalized_row:
            return normalized_row[normalized_candidate]
    return None


def build_student_identity(row: dict[str, Any]) -> dict[str, str]:
    """
    Construye la identidad base del estudiante a partir de la fila cruda,
    tolerando variantes comunes de encabezados.
    """
    normalized_row = _build_normalized_row_lookup(row)

    raw_id = _get_first_matching_value(
        normalized_row,
        IDENTITY_COLUMN_CANDIDATES["id_estudiante"],
    )
    raw_name = _get_first_matching_value(
        normalized_row,
        IDENTITY_COLUMN_CANDIDATES["nombre_estudiante"],
    )
    raw_numero = _get_first_matching_value(
        normalized_row,
        IDENTITY_COLUMN_CANDIDATES["numero"],
    )
    raw_curso = _get_first_matching_value(
        normalized_row,
        IDENTITY_COLUMN_CANDIDATES["curso"],
    )
    raw_prof_titular = _get_first_matching_value(
        normalized_row,
        IDENTITY_COLUMN_CANDIDATES["prof_titular"],
    )

    return {
        "id_estudiante": normalize_sheet_identifier(raw_id),
        "nombre_estudiante": normalize_text(raw_name),
        "numero": normalize_sheet_identifier(raw_numero),
        "curso": normalize_text(raw_curso),
        "prof_titular": normalize_text(raw_prof_titular),
    }


def initialize_subject_period_structure() -> dict[str, dict[str, Any]]:
    return {
        "P1": {"blocks": {}},
        "P2": {"blocks": {}},
        "P3": {"blocks": {}},
        "P4": {"blocks": {}},
    }


def parse_student_row(row: dict[str, Any]) -> dict[str, Any]:
    """
    Convierte una fila cruda del sheet en una estructura académica utilizable.
    """
    student = build_student_identity(row)
    subjects: dict[str, dict[str, Any]] = {}

    for raw_column_name, raw_value in row.items():
        normalized_column_name = normalize_header_key(raw_column_name)

        if not is_academic_block_column(normalized_column_name):
            continue

        parsed_column = parse_academic_block_column(normalized_column_name)
        if not parsed_column:
            continue

        subject_code = parsed_column["subject_code"]
        subject_name = parsed_column["subject_name"]
        block_code = parsed_column["block_code"]
        block_label = parsed_column["block_label"]
        period_code = parsed_column["period_code"]

        if subject_code not in subjects:
            subjects[subject_code] = {
                "subject_code": subject_code,
                "subject_name": subject_name,
                "periods": initialize_subject_period_structure(),
            }

        score = safe_float(raw_value)

        subjects[subject_code]["periods"][period_code]["blocks"][block_code] = {
            "block_code": block_code,
            "block_label": block_label,
            "score": score,
            "column_name": normalized_column_name,
        }

    return {
        "student": student,
        "subjects": subjects,
    }


def parse_student_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    parsed_rows: list[dict[str, Any]] = []

    for row in rows:
        if not isinstance(row, dict):
            continue
        parsed_rows.append(parse_student_row(row))

    return parsed_rows


def get_detected_academic_subject_codes(rows: list[dict[str, Any]]) -> list[str]:
    detected: set[str] = set()

    for row in rows:
        if not isinstance(row, dict):
            continue

        for raw_column_name in row.keys():
            parsed = parse_academic_block_column(str(raw_column_name))
            if parsed:
                detected.add(parsed["subject_code"])

    return sorted(detected)


def get_detected_academic_subjects(rows: list[dict[str, Any]]) -> list[dict[str, str]]:
    subject_codes = get_detected_academic_subject_codes(rows)

    return [
        {
            "subject_code": subject_code,
            "subject_name": get_subject_name(subject_code),
        }
        for subject_code in subject_codes
    ]


def get_supported_period_codes() -> list[str]:
    return ["P1", "P2", "P3", "P4"]


def get_supported_block_codes() -> list[str]:
    return ["C1", "C2", "C3", "C4"]