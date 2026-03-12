from typing import Any

from app.data.fetchers.google_sheets import load_primer_ciclo, load_segundo_ciclo
from app.data.transformers.student_profile import build_subjects, build_modules
from app.utils.helpers import safe_value


def normalize_student_id(value) -> str:
    text = safe_value(value)

    if text.endswith(".0"):
        text = text[:-2]

    return text


def normalize_student_number(value) -> str:
    text = safe_value(value)

    if text.endswith(".0"):
        text = text[:-2]

    return text


def normalize_course_name(value) -> str:
    text = safe_value(value).strip()

    if not text:
        return ""

    text = " ".join(text.split())
    return text


def is_real_value(value: Any) -> bool:
    if value is None:
        return False

    if isinstance(value, str):
        cleaned = value.strip()
        if cleaned in ("", "-", "—", "N/A", "NA", "null", "None"):
            return False

    return True


def normalize_grade_value(value: Any) -> Any:
    if value is None:
        return None

    if isinstance(value, str):
        value = value.strip()
        if value == "":
            return None

    return value


def get_first_existing_value(data: dict, keys: list[str], default=None):
    for key in keys:
        if key in data:
            return data.get(key)
    return default


def build_visible_module_ras(module: dict) -> list[dict]:
    """
    Construye una lista dinámica de RA visibles para un módulo.
    Solo incluye los RA que realmente tengan nota.
    """
    ras = []

    for i in range(1, 11):
        possible_keys = [
            f"ra{i}",
            f"RA{i}",
            f"ra_{i}",
            f"RA_{i}",
        ]

        value = normalize_grade_value(get_first_existing_value(module, possible_keys))

        if is_real_value(value):
            ras.append({
                "label": f"RA{i}",
                "value": value,
            })

    return ras


def enrich_module(module: dict) -> dict:
    """
    Enriquece cada módulo con:
    - ras_visibles
    - valores normalizados de CF y situación
    - nombre de módulo consistente
    """
    module_name = get_first_existing_value(
        module,
        ["modulo", "MODULO", "nombre_modulo", "NOMBRE_MODULO"],
        default="Módulo"
    )

    cf = normalize_grade_value(
        get_first_existing_value(module, ["cf", "CF"])
    )

    situ_a = normalize_grade_value(
        get_first_existing_value(module, ["situ_a", "SITU_A"])
    )

    situ_r = normalize_grade_value(
        get_first_existing_value(module, ["situ_r", "SITU_R"])
    )

    enriched = dict(module)
    enriched["modulo"] = safe_value(module_name)
    enriched["cf"] = cf
    enriched["situ_a"] = situ_a
    enriched["situ_r"] = situ_r
    enriched["ras_visibles"] = build_visible_module_ras(module)

    return enriched


def enrich_modules_for_second_cycle(modules: list[dict]) -> list[dict]:
    if not modules:
        return []

    return [enrich_module(module) for module in modules]


def filter_modules_with_visible_ras(modules: list[dict]) -> list[dict]:
    """
    Conserva solo los módulos que tengan al menos un RA con nota.
    Esta lista será útil para el boletín 'solo módulos'
    y también para el boletín mixto.
    """
    return [module for module in modules if module.get("ras_visibles")]


def build_student_result_from_row(row, cycle: str) -> dict:
    if cycle == "Primer_Ciclo":
        return {
            "found": True,
            "cycle": "Primer_Ciclo",
            "student": {
                "id_estudiante": safe_value(row.get("ID_ESTUDIANTE")),
                "nombre_estudiante": safe_value(row.get("NOMBRE_ESTUDIANTE")),
                "numero": normalize_student_number(row.get("NUMERO")),
                "curso": safe_value(row.get("CURSO")),
                "prof_titular": safe_value(row.get("PROF_TITULAR")),
                "asistencia_anual_pct": safe_value(row.get("ASIST_ANUAL_PCT")),
                "situacion_promovido": safe_value(row.get("SITUACION_PROMOVIDO")),
                "situacion_repitente": safe_value(row.get("SITUACION_REPITENTE")),
                "comentario_final": safe_value(row.get("COMENTARIO_FINAL")),
                "subjects": build_subjects(row, "Primer_Ciclo"),
                "modules": [],
                "modules_with_ras": []
            }
        }

    if cycle == "Segundo_Ciclo":
        raw_modules = build_modules(row)
        enriched_modules = enrich_modules_for_second_cycle(raw_modules)
        modules_with_ras = filter_modules_with_visible_ras(enriched_modules)

        return {
            "found": True,
            "cycle": "Segundo_Ciclo",
            "student": {
                "id_estudiante": safe_value(row.get("ID_ESTUDIANTE")),
                "nombre_estudiante": safe_value(row.get("NOMBRE_ESTUDIANTE")),
                "numero": normalize_student_number(row.get("NUMERO")),
                "curso": safe_value(row.get("CURSO")),
                "prof_titular": safe_value(row.get("PROF_TITULAR")),
                "situacion_promovido": safe_value(row.get("SITUACION_PROMOVIDO")),
                "situacion_repitente": safe_value(row.get("SITUACION_REPITENTE")),
                "situacion_pendiente": safe_value(row.get("SITUACION_PENDIENTE")),
                "comentario_final": safe_value(row.get("COMENTARIO_FINAL")),
                "subjects": build_subjects(row, "Segundo_Ciclo"),
                "modules": enriched_modules,
                "modules_with_ras": modules_with_ras
            }
        }

    raise ValueError("Ciclo no válido. Debe ser 'Primer_Ciclo' o 'Segundo_Ciclo'.")


def _prepare_cycle_dataframe(cycle: str):
    if cycle == "Primer_Ciclo":
        df = load_primer_ciclo().copy()
    elif cycle == "Segundo_Ciclo":
        df = load_segundo_ciclo().copy()
    else:
        raise ValueError("Ciclo no válido. Debe ser 'Primer_Ciclo' o 'Segundo_Ciclo'.")

    if "ID_ESTUDIANTE" in df.columns:
        df["ID_ESTUDIANTE"] = df["ID_ESTUDIANTE"].apply(normalize_student_id)

    if "CURSO" in df.columns:
        df["CURSO"] = df["CURSO"].apply(normalize_course_name)

    return df


def get_available_courses(cycle: str) -> list[str]:
    """
    Devuelve la lista única y ordenada de cursos disponibles para un ciclo.
    """
    df = _prepare_cycle_dataframe(cycle)

    if "CURSO" not in df.columns:
        return []

    courses = sorted(
        {
            course
            for course in df["CURSO"].dropna().tolist()
            if normalize_course_name(course)
        }
    )

    return courses


def get_available_courses_by_cycle() -> dict:
    """
    Devuelve cursos separados por ciclo.
    """
    return {
        "Primer_Ciclo": get_available_courses("Primer_Ciclo"),
        "Segundo_Ciclo": get_available_courses("Segundo_Ciclo"),
    }


def get_student_cycle_by_id(student_id: str) -> dict:
    """
    Permite detectar el ciclo del estudiante sin devolver todavía el boletín completo.
    """
    result = find_student_by_id(student_id)

    if not result.get("found"):
        return {
            "found": False,
            "message": result.get("message", f"No se encontró ningún estudiante con el ID {student_id}")
        }

    return {
        "found": True,
        "cycle": result["cycle"],
        "student_id": result["student"].get("id_estudiante"),
        "student_name": result["student"].get("nombre_estudiante"),
        "course": result["student"].get("curso"),
    }


def find_student_by_id(student_id: str) -> dict:
    student_id = normalize_student_id(student_id)

    primer = _prepare_cycle_dataframe("Primer_Ciclo")
    segundo = _prepare_cycle_dataframe("Segundo_Ciclo")

    student_primer = primer[primer["ID_ESTUDIANTE"] == student_id]
    if not student_primer.empty:
        row = student_primer.iloc[0]
        return build_student_result_from_row(row, "Primer_Ciclo")

    student_segundo = segundo[segundo["ID_ESTUDIANTE"] == student_id]
    if not student_segundo.empty:
        row = student_segundo.iloc[0]
        return build_student_result_from_row(row, "Segundo_Ciclo")

    return {
        "found": False,
        "message": f"No se encontró ningún estudiante con el ID {student_id}"
    }