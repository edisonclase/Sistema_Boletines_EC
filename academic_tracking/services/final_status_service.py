"""
final_status_service.py

Servicio para calcular la situación final del estudiante:
- Promovido
- Completivo
- Extraordinario
- Especial
- Evaluación especial de módulo formativo

Este servicio no altera el seguimiento por bloques de competencias.
"""

from __future__ import annotations

import re
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


def _normalize_course_text(value: Any) -> str:
    text = normalize_text(value)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _has_real_student_identity(row: dict[str, Any]) -> bool:
    student_id = normalize_text(row.get("ID_ESTUDIANTE"))
    student_name = normalize_text(row.get("NOMBRE_ESTUDIANTE"))
    course_name = normalize_text(row.get("CURSO"))

    return bool(student_id or student_name) and bool(course_name)


def _get_score(row: dict[str, Any], column_name: str) -> Optional[float]:
    return safe_float(row.get(column_name))


def _is_valid_score(value: Optional[float]) -> bool:
    return value is not None and value > 0


def _subject_has_any_data(row: dict[str, Any], subject_code: str) -> bool:
    columns = [
        f"{subject_code}_CF_FINAL",
        f"{subject_code}_CCF",
        f"{subject_code}_CEXF",
        f"{subject_code}_CE_ESPECIAL",
    ]

    return any(_is_valid_score(_get_score(row, column)) for column in columns)


def _module_has_any_data(row: dict[str, Any], module_prefix: str) -> bool:
    module_name = normalize_text(row.get(f"{module_prefix}_NOMBRE"))
    module_cf = _get_score(row, f"{module_prefix}_CF")

    return bool(module_name) or _is_valid_score(module_cf)


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

    student_id = normalize_text(row.get("ID_ESTUDIANTE"))
    student_name = normalize_text(row.get("NOMBRE_ESTUDIANTE"))
    numero = normalize_text(row.get("NUMERO"))
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

    if not academic_results and not module_results:
        return None

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

    if subjects_to_especial:
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
        student_id = normalize_text(item.get("student_id"))
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


def build_final_status_report(rows: list[dict[str, Any]]) -> dict[str, Any]:
    analyzed_rows: list[dict[str, Any]] = []

    for row in rows:
        student_status = analyze_student_final_status(row)
        if student_status:
            analyzed_rows.append(student_status)

    student_rows = _deduplicate_students(analyzed_rows)

    promoted_students = [
        item for item in student_rows if item["final_status"] == STATUS_PROMOVIDO
    ]

    completivo_students = [
        item for item in student_rows if item["final_status"] == STATUS_COMPLETIVO
    ]

    extraordinario_students = [
        item for item in student_rows if item["final_status"] == STATUS_EXTRAORDINARIO
    ]

    especial_students = [
        item for item in student_rows if item["final_status"] == STATUS_ESPECIAL
    ]

    module_special_students = [
        item for item in student_rows if item["final_status"] == STATUS_MODULO_ESPECIAL
    ]

    return {
        "summary": {
            "total_students": len(student_rows),
            "promoted": len(promoted_students),
            "completivo": len(completivo_students),
            "extraordinario": len(extraordinario_students),
            "especial": len(especial_students),
            "modulo_especial": len(module_special_students),
        },
        "students": student_rows,
        "promoted_students": promoted_students,
        "completivo_students": completivo_students,
        "extraordinario_students": extraordinario_students,
        "especial_students": especial_students,
        "module_special_students": module_special_students,
    }