"""
final_status_service.py

Servicio para calcular la situación final del estudiante:
- Promovido
- Completivo
- Extraordinario
- Especial
- Evaluación especial de módulo formativo

Reglas importantes:
- La matrícula inscrita se cuenta por estudiantes únicos con ID, usando SEXO.
- Las estadísticas académicas solo cuentan estudiantes activos.
- Estudiantes transferidos, retirados, abandonaron o inactivos no cuentan en estadísticas de calificaciones.
"""

from __future__ import annotations

import re
import math
from typing import Any, Optional

from .parsing_service import normalize_text, safe_float


ACADEMIC_SUBJECTS = {
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

MODULE_PREFIXES = ["MOD1", "MOD2", "MOD3", "MOD4", "MOD5"]

MIN_PASS_SCORE = 70.0

STATUS_PROMOVIDO = "promovido"
STATUS_COMPLETIVO = "completivo"
STATUS_EXTRAORDINARIO = "extraordinario"
STATUS_ESPECIAL = "especial"
STATUS_MODULO_ESPECIAL = "modulo_especial"
STATUS_SIN_DATOS = "sin_datos"

INACTIVE_STATUS_WORDS = {
    "ABANDONO",
    "ABANDONÓ",
    "ABANDONO EL CENTRO",
    "ABANDONÓ EL CENTRO",
    "RETIRADO",
    "RETIRADA",
    "TRANSFERIDO",
    "TRANSFERIDA",
    "TRASLADADO",
    "TRASLADADA",
    "INACTIVO",
    "INACTIVA",
    "BAJA",
}

ACTIVE_STATUS_WORDS = {
    "ACTIVO",
    "ACTIVA",
    "INSCRITO",
    "INSCRITA",
    "MATRICULADO",
    "MATRICULADA",
}


def _clean_identifier_value(value: Any) -> str:
    if value is None:
        return ""

    if isinstance(value, float):
        if math.isnan(value):
            return ""
        if value.is_integer():
            return str(int(value))
        return str(value).strip()

    text = str(value).strip()

    if not text or text.lower() == "nan":
        return ""

    if text.endswith(".0"):
        text = text[:-2]

    return text


def _normalize_course_text(value: Any) -> str:
    text = normalize_text(value)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _normalize_status_text(value: Any) -> str:
    text = normalize_text(value).upper()
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _normalize_sex(value: Any) -> str:
    text = normalize_text(value).upper().strip()

    if text in {"M", "MASCULINO", "VARON", "VARÓN", "HOMBRE"}:
        return "Masculino"

    if text in {"F", "FEMENINO", "HEMBRA", "MUJER"}:
        return "Femenino"

    return "No especificado"


def _get_row_value_flexible(row: dict[str, Any], possible_keys: list[str]) -> Any:
    normalized_lookup = {
        str(key).strip().upper(): value
        for key, value in row.items()
        if key is not None
    }

    for key in possible_keys:
        normalized_key = key.strip().upper()
        if normalized_key in normalized_lookup:
            return normalized_lookup[normalized_key]

    return None


def _get_student_id(row: dict[str, Any]) -> str:
    return _clean_identifier_value(
        _get_row_value_flexible(
            row,
            ["ID_ESTUDIANTE", "ID ESTUDIANTE", "ID", "MATRICULA", "MATRÍCULA"],
        )
    )


def _get_student_name(row: dict[str, Any]) -> str:
    return normalize_text(
        _get_row_value_flexible(
            row,
            ["NOMBRE_ESTUDIANTE", "NOMBRE ESTUDIANTE", "NOMBRE", "ESTUDIANTE"],
        )
    )


def _get_student_sex(row: dict[str, Any]) -> str:
    return _normalize_sex(
        _get_row_value_flexible(
            row,
            ["SEXO", "GENERO", "GÉNERO"],
        )
    )


def _get_student_status(row: dict[str, Any]) -> str:
    return _normalize_status_text(
        _get_row_value_flexible(
            row,
            ["ESTADO", "STATUS", "CONDICION", "CONDICIÓN"],
        )
    )


def _is_active_student(row: dict[str, Any]) -> bool:
    status = _get_student_status(row)

    if not status:
        return True

    if status in INACTIVE_STATUS_WORDS:
        return False

    if status in ACTIVE_STATUS_WORDS:
        return True

    for inactive_word in INACTIVE_STATUS_WORDS:
        if inactive_word in status:
            return False

    return True


def _has_real_student_identity(row: dict[str, Any]) -> bool:
    student_id = _get_student_id(row)
    student_name = _get_student_name(row)
    course_name = normalize_text(row.get("CURSO"))

    return bool(student_id or student_name) and bool(course_name)


def _get_score(row: dict[str, Any], column_name: str) -> Optional[float]:
    return safe_float(row.get(column_name))


def _is_valid_score(value: Optional[float]) -> bool:
    return value is not None


def _subject_has_any_data(row: dict[str, Any], subject_code: str) -> bool:
    columns = [
        f"{subject_code}_CF_FINAL",
        f"{subject_code}_CCF",
        f"{subject_code}_CEXF",
        f"{subject_code}_CE_ESPECIAL",
    ]

    for column in columns:
        if column not in row:
            continue

        raw_value = row.get(column)

        if raw_value is None:
            continue

        if str(raw_value).strip() != "":
            return True

    return False


def _module_has_any_data(row: dict[str, Any], module_prefix: str) -> bool:
    module_name = normalize_text(row.get(f"{module_prefix}_NOMBRE"))

    if module_name:
        return True

    column_name = f"{module_prefix}_CF"

    if column_name not in row:
        return False

    raw_value = row.get(column_name)

    if raw_value is None:
        return False

    return str(raw_value).strip() != ""


def analyze_academic_subject(
    row: dict[str, Any],
    subject_code: str,
) -> Optional[dict[str, Any]]:
    if f"{subject_code}_CF_FINAL" not in row:
        return None

    if not _subject_has_any_data(row, subject_code):
        return None

    subject_name = ACADEMIC_SUBJECTS.get(subject_code, subject_code)

    cf_final = _get_score(row, f"{subject_code}_CF_FINAL")
    ccf = _get_score(row, f"{subject_code}_CCF")
    cexf = _get_score(row, f"{subject_code}_CEXF")
    ce_especial = _get_score(row, f"{subject_code}_CE_ESPECIAL")

    needs_completivo = _is_valid_score(cf_final) and cf_final < MIN_PASS_SCORE
    needs_extraordinario = _is_valid_score(ccf) and ccf < MIN_PASS_SCORE
    needs_especial = _is_valid_score(cexf) and cexf < MIN_PASS_SCORE

    passed = (
        _is_valid_score(cf_final)
        and cf_final >= MIN_PASS_SCORE
        and not needs_completivo
        and not needs_extraordinario
        and not needs_especial
    )

    return {
        "subject_code": subject_code,
        "subject_name": subject_name,
        "cf_final": cf_final,
        "ccf": ccf,
        "cexf": cexf,
        "ce_especial": ce_especial,
        "passed": passed,
        "needs_completivo": needs_completivo,
        "needs_extraordinario": needs_extraordinario,
        "needs_especial": needs_especial,
    }


def analyze_module(
    row: dict[str, Any],
    module_prefix: str,
) -> Optional[dict[str, Any]]:
    if f"{module_prefix}_CF" not in row:
        return None

    if not _module_has_any_data(row, module_prefix):
        return None

    module_name = normalize_text(row.get(f"{module_prefix}_NOMBRE"))
    module_cf = _get_score(row, f"{module_prefix}_CF")

    passed = _is_valid_score(module_cf) and module_cf >= MIN_PASS_SCORE
    needs_special_module_evaluation = _is_valid_score(module_cf) and module_cf < MIN_PASS_SCORE

    return {
        "module_code": module_prefix,
        "module_name": module_name or module_prefix,
        "module_cf": module_cf,
        "passed": passed,
        "needs_special_module_evaluation": needs_special_module_evaluation,
    }


def analyze_student_final_status(row: dict[str, Any]) -> Optional[dict[str, Any]]:
    if not _has_real_student_identity(row):
        return None

    student_id = _get_student_id(row)
    student_name = _get_student_name(row)
    sex = _get_student_sex(row)
    status_text = _get_student_status(row)
    is_active = _is_active_student(row)

    numero = _clean_identifier_value(row.get("NUMERO"))
    course_name = _normalize_course_text(row.get("CURSO"))
    prof_titular = normalize_text(row.get("PROF_TITULAR"))

    academic_results: list[dict[str, Any]] = []
    module_results: list[dict[str, Any]] = []

    for subject_code in ACADEMIC_SUBJECTS:
        subject_result = analyze_academic_subject(row, subject_code)
        if subject_result:
            academic_results.append(subject_result)

    for module_prefix in MODULE_PREFIXES:
        module_result = analyze_module(row, module_prefix)
        if module_result:
            module_results.append(module_result)

    subjects_to_completivo = [
        item for item in academic_results if item["needs_completivo"]
    ]

    subjects_to_extraordinario = [
        item for item in academic_results if item["needs_extraordinario"]
    ]

    subjects_to_especial = [
        item for item in academic_results if item["needs_especial"]
    ]

    modules_to_special_evaluation = [
        item for item in module_results if item["needs_special_module_evaluation"]
    ]

    if not academic_results and not module_results:
        final_status = STATUS_SIN_DATOS
        final_status_label = "Sin calificaciones finales"

    elif subjects_to_especial:
        final_status = STATUS_ESPECIAL
        final_status_label = "Evaluación especial"

    elif subjects_to_extraordinario:
        final_status = STATUS_EXTRAORDINARIO
        final_status_label = "Extraordinario"

    elif subjects_to_completivo:
        final_status = STATUS_COMPLETIVO
        final_status_label = "Completivo"

    elif modules_to_special_evaluation:
        final_status = STATUS_MODULO_ESPECIAL
        final_status_label = "Evaluación especial de módulo formativo"

    else:
        final_status = STATUS_PROMOVIDO
        final_status_label = "Promovido"

    promoted = final_status == STATUS_PROMOVIDO

    return {
        "student_id": student_id,
        "student_name": student_name,
        "sex": sex,
        "estado": status_text or "Activo",
        "is_active": is_active,
        "numero": numero,
        "course_name": course_name,
        "prof_titular": prof_titular,
        "promoted": promoted,
        "final_status": final_status,
        "final_status_label": final_status_label,
        "academic_results": academic_results,
        "module_results": module_results,
        "subjects_to_completivo": subjects_to_completivo,
        "subjects_to_extraordinario": subjects_to_extraordinario,
        "subjects_to_especial": subjects_to_especial,
        "modules_to_special_evaluation": modules_to_special_evaluation,
    }


def _deduplicate_students(
    student_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    unique: dict[tuple[str, str], dict[str, Any]] = {}

    for item in student_rows:
        student_id = _clean_identifier_value(item.get("student_id"))
        student_name = normalize_text(item.get("student_name"))
        course_name = normalize_text(item.get("course_name"))

        key = (
            student_id or student_name,
            course_name,
        )

        if not key[0] or not key[1]:
            continue

        unique[key] = item

    return list(unique.values())


def _count_by_sex(student_rows: list[dict[str, Any]]) -> dict[str, int]:
    counts = {
        "masculino": 0,
        "femenino": 0,
        "no_especificado": 0,
    }

    for item in student_rows:
        sex = item.get("sex")

        if sex == "Masculino":
            counts["masculino"] += 1
        elif sex == "Femenino":
            counts["femenino"] += 1
        else:
            counts["no_especificado"] += 1

    return counts


def build_final_status_report(rows: list[dict[str, Any]]) -> dict[str, Any]:
    analyzed_rows: list[dict[str, Any]] = []

    for row in rows:
        student_status = analyze_student_final_status(row)
        if student_status:
            analyzed_rows.append(student_status)

    enrolled_students = _deduplicate_students(analyzed_rows)

    active_students = [
        item for item in enrolled_students if item.get("is_active") is True
    ]

    inactive_students = [
        item for item in enrolled_students if item.get("is_active") is False
    ]

    promoted_students = [
        item for item in active_students if item["final_status"] == STATUS_PROMOVIDO
    ]

    completivo_students = [
        item for item in active_students if item["final_status"] == STATUS_COMPLETIVO
    ]

    extraordinario_students = [
        item for item in active_students if item["final_status"] == STATUS_EXTRAORDINARIO
    ]

    especial_students = [
        item for item in active_students if item["final_status"] == STATUS_ESPECIAL
    ]

    module_special_students = [
        item for item in active_students if item["final_status"] == STATUS_MODULO_ESPECIAL
    ]

    sin_datos_students = [
        item for item in active_students if item["final_status"] == STATUS_SIN_DATOS
    ]

    return {
        "summary": {
            "total_enrolled_students": len(enrolled_students),
            "active_students": len(active_students),
            "inactive_students": len(inactive_students),
            "total_students": len(active_students),
            "promoted": len(promoted_students),
            "completivo": len(completivo_students),
            "extraordinario": len(extraordinario_students),
            "especial": len(especial_students),
            "modulo_especial": len(module_special_students),
            "sin_datos": len(sin_datos_students),
            "enrolled_by_sex": _count_by_sex(enrolled_students),
            "active_by_sex": _count_by_sex(active_students),
        },
        "students": active_students,
        "enrolled_students": enrolled_students,
        "inactive_students": inactive_students,
        "promoted_students": promoted_students,
        "completivo_students": completivo_students,
        "extraordinario_students": extraordinario_students,
        "especial_students": especial_students,
        "module_special_students": module_special_students,
        "sin_datos_students": sin_datos_students,
    }