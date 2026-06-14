"""
final_statistics_service.py

Servicio para construir la Estadística General Final del Año Escolar.

Calcula:
- Inscritos
- Activos
- Inactivos
- Abandono / transferidos / retirados
- Promovidos sin completivo
- Estudiantes que fueron a completivo
- Estudiantes que fueron a extraordinario
- Estudiantes en especial
- Promovidos finales
- No promovidos / repitentes

Incluye desglose por:
- Ciclo
- Grado
- Sección / área técnica
- Sexo

Reglas confirmadas:
- Completivo asignaturas: *_CF_AREA < 70
- Extraordinario asignaturas: *_CCF < 70
- Módulos: MODx_CF < 70 no van a extraordinario; se consideran no promovidos del grado técnico.
"""

from __future__ import annotations

import math
import unicodedata
from collections import defaultdict
from typing import Any, Optional


ACADEMIC_SUBJECTS_PRIMER_CICLO = {
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

ACADEMIC_SUBJECTS_SEGUNDO_CICLO = {
    "LEN": "Lengua Española",
    "ING": "Inglés",
    "MAT": "Matemática",
    "SOC": "Ciencias Sociales",
    "NAT": "Ciencias de la Naturaleza",
    "ART": "Educación Artística",
    "FIS": "Educación Física",
    "FOR": "Formación Humana",
}


def _normalize_text(value: Any) -> str:
    if value is None:
        return ""

    text = str(value).strip()

    if text.lower() == "nan":
        return ""

    if text.endswith(".0"):
        number_part = text[:-2]

        if number_part.isdigit():
            return number_part

    return text


def _normalize_key(value: Any) -> str:
    text = _normalize_text(value).upper()
    text = unicodedata.normalize("NFD", text)
    text = "".join(char for char in text if unicodedata.category(char) != "Mn")
    return text.strip()


def _safe_float(value: Any) -> Optional[float]:
    if value is None:
        return None

    text = str(value).strip()

    if not text or text.lower() == "nan":
        return None

    text = text.replace("%", "").strip()

    if "/" in text:
        text = text.split("/", 1)[0].strip()

    try:
        number = float(text)
    except ValueError:
        return None

    if math.isnan(number):
        return None

    return number


def _format_percent(value: float) -> str:
    return f"{value:.1f}%"


def _percent(part: int, total: int) -> float:
    if total <= 0:
        return 0.0

    return round((part / total) * 100, 1)


def _is_active_status(status: Any) -> bool:
    return _normalize_key(status) in {"ACTIVO", "ACTIVA"}


def _is_inactive_status(status: Any) -> bool:
    status_key = _normalize_key(status)

    return status_key in {
        "ABANDONO",
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


def _detect_cycle(row: dict[str, Any], ciclo: Optional[str] = None) -> str:
    if ciclo:
        return ciclo

    course_name = _normalize_text(row.get("CURSO"))
    course_key = _normalize_key(course_name)

    primer_ciclo_markers = {
        "1RO",
        "1ERO",
        "PRIMERO",
        "2DO",
        "SEGUNDO",
        "3RO",
        "TERCERO",
    }

    segundo_ciclo_markers = {
        "4TO",
        "CUARTO",
        "5TO",
        "QUINTO",
        "6TO",
        "SEXTO",
    }

    first_word = course_key.split(maxsplit=1)[0] if course_key else ""

    if first_word in primer_ciclo_markers:
        return "Primer Ciclo"

    if first_word in segundo_ciclo_markers:
        return "Segundo Ciclo"

    for module_number in range(1, 6):
        module_name = _normalize_text(row.get(f"MOD{module_number}_NOMBRE"))
        module_cf = _safe_float(row.get(f"MOD{module_number}_CF"))

        if module_name or module_cf is not None:
            return "Segundo Ciclo"

    return "Primer Ciclo"


def _split_course_name(course_name: Any) -> tuple[str, str]:
    text = _normalize_text(course_name)

    if not text:
        return "", ""

    parts = text.split(maxsplit=1)

    if len(parts) == 2:
        return parts[0].strip(), parts[1].strip()

    return text, ""


def _subject_catalog_for_cycle(cycle: str) -> dict[str, str]:
    if _normalize_key(cycle) == "SEGUNDO CICLO":
        return ACADEMIC_SUBJECTS_SEGUNDO_CICLO

    return ACADEMIC_SUBJECTS_PRIMER_CICLO


def _student_key(row: dict[str, Any]) -> tuple[str, str]:
    return (
        _normalize_text(row.get("ID_ESTUDIANTE")),
        _normalize_text(row.get("CURSO")),
    )


def _matches_filters(
    *,
    row: dict[str, Any],
    ciclo: Optional[str],
    grado: Optional[str],
    seccion: Optional[str],
    sexo: Optional[str],
) -> bool:
    detected_cycle = _detect_cycle(row, ciclo=None)
    course_name = _normalize_text(row.get("CURSO"))
    raw_grade, raw_section = _split_course_name(course_name)

    if ciclo and _normalize_key(detected_cycle) != _normalize_key(ciclo):
        return False

    if grado and _normalize_text(raw_grade) != _normalize_text(grado):
        return False

    if seccion and _normalize_text(raw_section) != _normalize_text(seccion):
        return False

    if sexo and _normalize_key(row.get("SEXO")) != _normalize_key(sexo):
        return False

    return True


def _student_went_to_completivo(
    row: dict[str, Any],
    *,
    min_score: float = 70.0,
) -> bool:
    cycle = _detect_cycle(row)
    subject_catalog = _subject_catalog_for_cycle(cycle)

    for subject_code in subject_catalog:
        cf_area = _safe_float(row.get(f"{subject_code}_CF_AREA"))

        if cf_area is not None and cf_area < min_score:
            return True

    if _normalize_key(cycle) == "SEGUNDO CICLO":
        for module_number in range(1, 6):
            module_cf = _safe_float(row.get(f"MOD{module_number}_CF"))

            if module_cf is not None and module_cf < min_score:
                return True

    return False


def _student_went_to_extraordinario(
    row: dict[str, Any],
    *,
    min_score: float = 70.0,
) -> bool:
    cycle = _detect_cycle(row)
    subject_catalog = _subject_catalog_for_cycle(cycle)

    for subject_code in subject_catalog:
        ccf = _safe_float(row.get(f"{subject_code}_CCF"))

        if ccf is not None and ccf < min_score:
            return True

    return False


def _student_went_to_especial(
    row: dict[str, Any],
    *,
    min_score: float = 70.0,
) -> bool:
    """
    Regla inicial:
    - Si *_CEXF existe y es menor de 70, pasa a especial.
    - Esta regla puede ajustarse cuando se valide formalmente el módulo Especial.
    """
    cycle = _detect_cycle(row)
    subject_catalog = _subject_catalog_for_cycle(cycle)

    for subject_code in subject_catalog:
        cexf = _safe_float(row.get(f"{subject_code}_CEXF"))

        if cexf is not None and cexf < min_score:
            return True

    return False


def _student_has_failed_module(
    row: dict[str, Any],
    *,
    min_score: float = 70.0,
) -> bool:
    cycle = _detect_cycle(row)

    if _normalize_key(cycle) != "SEGUNDO CICLO":
        return False

    for module_number in range(1, 6):
        module_cf = _safe_float(row.get(f"MOD{module_number}_CF"))

        if module_cf is not None and module_cf < min_score:
            return True

    return False


def _get_subject_final_status(
    row: dict[str, Any],
    subject_code: str,
    *,
    min_score: float = 70.0,
) -> bool:
    cf_area = _safe_float(row.get(f"{subject_code}_CF_AREA"))
    ccf = _safe_float(row.get(f"{subject_code}_CCF"))
    cexf = _safe_float(row.get(f"{subject_code}_CEXF"))
    cf_final = _safe_float(row.get(f"{subject_code}_CF_FINAL"))

    # Si llegó a especial y tiene CF_FINAL, esa es la última referencia.
    if cf_final is not None:
        return cf_final >= min_score

    # Si llegó a extraordinario, se evalúa CEXF.
    if cexf is not None:
        return cexf >= min_score

    # Si llegó a completivo, se evalúa CCF.
    if ccf is not None:
        return ccf >= min_score

    # Si no fue a procesos, se evalúa CF_AREA.
    if cf_area is not None:
        return cf_area >= min_score

    return True


def _is_promoted_final(
    row: dict[str, Any],
    *,
    min_score: float = 70.0,
) -> bool:
    cycle = _detect_cycle(row)
    subject_catalog = _subject_catalog_for_cycle(cycle)

    for subject_code in subject_catalog:
        if not _get_subject_final_status(
            row,
            subject_code,
            min_score=min_score,
        ):
            return False

    if _student_has_failed_module(row, min_score=min_score):
        return False

    return True


def _build_empty_counter() -> dict[str, Any]:
    return {
        "inscritos": 0,
        "activos": 0,
        "inactivos": 0,
        "abandono_transferido": 0,
        "promovidos_sin_completivo": 0,
        "fueron_completivo": 0,
        "fueron_extraordinario": 0,
        "fueron_especial": 0,
        "promovidos_finales": 0,
        "no_promovidos": 0,
    }


def _counter_to_row(label: str, counter: dict[str, Any]) -> dict[str, Any]:
    inscritos = counter["inscritos"]
    activos = counter["activos"]

    row = {
        "label": label,
        **counter,
        "percentages": {
            "activos_sobre_inscritos": _format_percent(_percent(counter["activos"], inscritos)),
            "inactivos_sobre_inscritos": _format_percent(_percent(counter["inactivos"], inscritos)),
            "abandono_transferido_sobre_inscritos": _format_percent(_percent(counter["abandono_transferido"], inscritos)),
            "promovidos_sin_completivo_sobre_activos": _format_percent(_percent(counter["promovidos_sin_completivo"], activos)),
            "completivo_sobre_activos": _format_percent(_percent(counter["fueron_completivo"], activos)),
            "extraordinario_sobre_activos": _format_percent(_percent(counter["fueron_extraordinario"], activos)),
            "especial_sobre_activos": _format_percent(_percent(counter["fueron_especial"], activos)),
            "promovidos_finales_sobre_activos": _format_percent(_percent(counter["promovidos_finales"], activos)),
            "no_promovidos_sobre_activos": _format_percent(_percent(counter["no_promovidos"], activos)),
        },
    }

    return row


def build_final_statistics_report(
    *,
    rows: list[dict[str, Any]],
    center_id: Optional[Any] = None,
    school_year: Optional[str] = None,
    ciclo: Optional[str] = None,
    grado: Optional[str] = None,
    seccion: Optional[str] = None,
    sexo: Optional[str] = None,
    min_score: float = 70.0,
) -> dict[str, Any]:
    total_counter = _build_empty_counter()

    by_cycle: dict[str, dict[str, Any]] = defaultdict(_build_empty_counter)
    by_grade: dict[str, dict[str, Any]] = defaultdict(_build_empty_counter)
    by_section: dict[str, dict[str, Any]] = defaultdict(_build_empty_counter)
    by_sex: dict[str, dict[str, Any]] = defaultdict(_build_empty_counter)

    processed_students: set[tuple[str, str]] = set()

    for row in rows or []:
        if not isinstance(row, dict):
            continue

        if not _matches_filters(
            row=row,
            ciclo=ciclo,
            grado=grado,
            seccion=seccion,
            sexo=sexo,
        ):
            continue

        student_key = _student_key(row)

        if not student_key[0]:
            continue

        if student_key in processed_students:
            continue

        processed_students.add(student_key)

        detected_cycle = _detect_cycle(row)
        course_name = _normalize_text(row.get("CURSO"))
        raw_grade, raw_section = _split_course_name(course_name)
        sex_label = _normalize_text(row.get("SEXO")) or "No especificado"
        status = row.get("ESTADO")

        is_active = _is_active_status(status)
        is_inactive = not is_active
        is_abandono_transferido = _is_inactive_status(status)

        went_completivo = False
        went_extraordinario = False
        went_especial = False
        promoted_final = False
        promoted_without_completivo = False
        no_promoted = False

        if is_active:
            went_completivo = _student_went_to_completivo(
                row,
                min_score=min_score,
            )
            went_extraordinario = _student_went_to_extraordinario(
                row,
                min_score=min_score,
            )
            went_especial = _student_went_to_especial(
                row,
                min_score=min_score,
            )
            failed_module = _student_has_failed_module(
                row,
                min_score=min_score,
            )
            promoted_final = _is_promoted_final(row, min_score=min_score)

            promoted_without_completivo = (
                promoted_final
                and not went_completivo
                and not went_extraordinario
                and not went_especial
                and not failed_module
            )

            no_promoted = (
                not promoted_final
                or failed_module
            )

        counters = [
            total_counter,
            by_cycle[detected_cycle or "Sin ciclo"],
            by_grade[raw_grade or "Sin grado"],
            by_section[raw_section or "Sin sección"],
            by_sex[sex_label],
        ]

        for counter in counters:
            counter["inscritos"] += 1

            if is_active:
                counter["activos"] += 1
            else:
                counter["inactivos"] += 1

            if is_abandono_transferido:
                counter["abandono_transferido"] += 1

            if went_completivo:
                counter["fueron_completivo"] += 1

            if went_extraordinario:
                counter["fueron_extraordinario"] += 1

            if went_especial:
                counter["fueron_especial"] += 1

            if promoted_without_completivo:
                counter["promovidos_sin_completivo"] += 1

            if promoted_final:
                counter["promovidos_finales"] += 1

            if no_promoted:
                counter["no_promovidos"] += 1

    report = {
        "metadata": {
            "center_id": center_id,
            "school_year": school_year,
            "filters": {
                "ciclo": ciclo,
                "grado": grado,
                "seccion": seccion,
                "sexo": sexo,
            },
            "notes": [
                "Los porcentajes sobre inscritos incluyen estudiantes activos e inactivos.",
                "Los porcentajes sobre activos excluyen abandono, transferidos, retirados e inactivos.",
                "Un estudiante se cuenta una sola vez por proceso, aunque tenga varias asignaturas pendientes.",
                "Los módulos formativos no pasan a extraordinario.",
            ],
        },
        "summary": _counter_to_row("Total general", total_counter),
        "tables": {
            "by_cycle": [
                _counter_to_row(label, counter)
                for label, counter in sorted(by_cycle.items())
            ],
            "by_grade": [
                _counter_to_row(label, counter)
                for label, counter in sorted(by_grade.items())
            ],
            "by_section": [
                _counter_to_row(label, counter)
                for label, counter in sorted(by_section.items())
            ],
            "by_sex": [
                _counter_to_row(label, counter)
                for label, counter in sorted(by_sex.items())
            ],
        },
    }

    return report