"""
final_status_service.py

Servicio para calcular situación final del estudiante:
- Promovido
- Completivo
- Extraordinario
- Especial
- Evaluación especial de módulo formativo

No altera el seguimiento por bloques de competencias.
"""

from __future__ import annotations

from typing import Any, Optional

from .parsing_service import safe_float, normalize_text


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


def _get_score(row: dict[str, Any], column_name: str) -> Optional[float]:
    return safe_float(row.get(column_name))


def _is_reported(value: Optional[float]) -> bool:
    return value is not None and value > 0


def analyze_academic_subject(row: dict[str, Any], subject_code: str) -> dict[str, Any]:
    subject_name = ACADEMIC_SUBJECTS.get(subject_code, subject_code)

    cf_final = _get_score(row, f"{subject_code}_CF_FINAL")
    ccf = _get_score(row, f"{subject_code}_CCF")
    cexf = _get_score(row, f"{subject_code}_CEXF")
    ce_especial = _get_score(row, f"{subject_code}_CE_ESPECIAL")

    needs_completivo = _is_reported(cf_final) and cf_final < MIN_PASS_SCORE
    needs_extraordinario = _is_reported(ccf) and ccf < MIN_PASS_SCORE
    needs_especial = _is_reported(cexf) and cexf < MIN_PASS_SCORE

    passed = (
        _is_reported(cf_final)
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


def analyze_module(row: dict[str, Any], module_prefix: str) -> Optional[dict[str, Any]]:
    module_name = normalize_text(row.get(f"{module_prefix}_NOMBRE"))
    module_cf = _get_score(row, f"{module_prefix}_CF")

    if not module_name and module_cf is None:
        return None

    needs_special_module_evaluation = _is_reported(module_cf) and module_cf < MIN_PASS_SCORE

    return {
        "module_code": module_prefix,
        "module_name": module_name or module_prefix,
        "module_cf": module_cf,
        "passed": _is_reported(module_cf) and module_cf >= MIN_PASS_SCORE,
        "needs_special_module_evaluation": needs_special_module_evaluation,
    }


def analyze_student_final_status(row: dict[str, Any]) -> dict[str, Any]:
    student_id = normalize_text(row.get("ID_ESTUDIANTE"))
    student_name = normalize_text(row.get("NOMBRE_ESTUDIANTE"))
    numero = normalize_text(row.get("NUMERO"))
    course_name = normalize_text(row.get("CURSO"))
    prof_titular = normalize_text(row.get("PROF_TITULAR"))

    academic_results = []
    module_results = []

    for subject_code in ACADEMIC_SUBJECTS:
        if f"{subject_code}_CF_FINAL" in row:
            academic_results.append(analyze_academic_subject(row, subject_code))

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

    has_pending_academic = (
        bool(subjects_to_completivo)
        or bool(subjects_to_extraordinario)
        or bool(subjects_to_especial)
    )

    has_pending_modules = bool(modules_to_special_evaluation)

    promoted = not has_pending_academic and not has_pending_modules

    if subjects_to_especial:
        final_status = "especial"
        final_status_label = "Evaluación especial"
    elif subjects_to_extraordinario:
        final_status = "extraordinario"
        final_status_label = "Extraordinario"
    elif subjects_to_completivo:
        final_status = "completivo"
        final_status_label = "Completivo"
    elif modules_to_special_evaluation:
        final_status = "modulo_especial"
        final_status_label = "Evaluación especial de módulo formativo"
    else:
        final_status = "promovido"
        final_status_label = "Promovido"

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


def build_final_status_report(rows: list[dict[str, Any]]) -> dict[str, Any]:
    student_rows = [analyze_student_final_status(row) for row in rows]

    promoted_students = [
        item for item in student_rows if item["final_status"] == "promovido"
    ]

    completivo_students = [
        item for item in student_rows if item["final_status"] == "completivo"
    ]

    extraordinario_students = [
        item for item in student_rows if item["final_status"] == "extraordinario"
    ]

    especial_students = [
        item for item in student_rows if item["final_status"] == "especial"
    ]

    module_special_students = [
        item for item in student_rows if item["final_status"] == "modulo_especial"
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