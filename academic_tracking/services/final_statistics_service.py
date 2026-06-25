"""
final_statistics_service.py

Servicio para construir la Estadística General Final del Año Escolar.
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


def _normalize_sex_label(value: Any) -> str:
    sex_key = _normalize_key(value)

    if sex_key in {"MASCULINO", "M", "VARON"}:
        return "Masculino"

    if sex_key in {"FEMENINO", "F", "HEMBRA"}:
        return "Femenino"

    return "No especificado"


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


def _is_inactive_status(status: Any) -> bool:
    status_key = _normalize_key(status)

    inactive_words = {
        "ABANDONO",
        "ABANDONO EL CENTRO",
        "ABANDONO DEL CENTRO",
        "RETIRADO",
        "RETIRADA",
        "TRANSFERIDO",
        "TRANSFERIDA",
        "TRANFERIDO",
        "TRANFERIDA",
        "TRASLADADO",
        "TRASLADADA",
        "INACTIVO",
        "INACTIVA",
        "BAJA",
    }

    if not status_key:
        return False

    if status_key in inactive_words:
        return True

    return any(word in status_key for word in inactive_words)


def _is_active_status(status: Any) -> bool:
    return not _is_inactive_status(status)


def _detect_cycle(row: dict[str, Any], ciclo: Optional[str] = None) -> str:
    if ciclo:
        return ciclo

    course_name = _normalize_text(row.get("CURSO"))
    course_key = _normalize_key(course_name)
    first_word = course_key.split(maxsplit=1)[0] if course_key else ""

    if first_word in {"1RO", "1ERO", "PRIMERO", "2DO", "SEGUNDO", "3RO", "TERCERO"}:
        return "Primer Ciclo"

    if first_word in {"4TO", "CUARTO", "5TO", "QUINTO", "6TO", "SEXTO"}:
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


def _subject_status(
    row: dict[str, Any],
    subject_code: str,
    *,
    min_score: float = 70.0,
) -> dict[str, Any]:
    cf_area = _safe_float(row.get(f"{subject_code}_CF_AREA"))
    ccf = _safe_float(row.get(f"{subject_code}_CCF"))
    cexf = _safe_float(row.get(f"{subject_code}_CEXF"))
    ce_especial = _safe_float(row.get(f"{subject_code}_CE_ESPECIAL"))

    went_completivo = cf_area is not None and cf_area < min_score
    went_extraordinario = ccf is not None and ccf < min_score
    pending_after_extraordinario = cexf is not None and cexf < min_score
    failed_after_special = ce_especial is not None and ce_especial < min_score

    if ce_especial is not None:
        promoted = ce_especial >= min_score
    elif cexf is not None:
        promoted = cexf >= min_score
    elif ccf is not None:
        promoted = ccf >= min_score
    elif cf_area is not None:
        promoted = cf_area >= min_score
    else:
        promoted = True

    return {
        "promoted": promoted and not failed_after_special,
        "went_completivo": went_completivo,
        "went_extraordinario": went_extraordinario,
        "pending_after_extraordinario": pending_after_extraordinario,
        "failed_after_special": failed_after_special,
    }


def _student_went_to_completivo(
    row: dict[str, Any],
    *,
    min_score: float = 70.0,
) -> bool:
    cycle = _detect_cycle(row)
    subject_catalog = _subject_catalog_for_cycle(cycle)

    return any(
        _subject_status(row, subject_code, min_score=min_score)["went_completivo"]
        for subject_code in subject_catalog
    )


def _student_went_to_extraordinario(
    row: dict[str, Any],
    *,
    min_score: float = 70.0,
) -> bool:
    cycle = _detect_cycle(row)
    subject_catalog = _subject_catalog_for_cycle(cycle)

    return any(
        _subject_status(row, subject_code, min_score=min_score)["went_extraordinario"]
        for subject_code in subject_catalog
    )


def _count_pending_after_extraordinario(
    row: dict[str, Any],
    *,
    min_score: float = 70.0,
) -> int:
    cycle = _detect_cycle(row)
    subject_catalog = _subject_catalog_for_cycle(cycle)

    return sum(
        1
        for subject_code in subject_catalog
        if _subject_status(row, subject_code, min_score=min_score)["pending_after_extraordinario"]
    )


def _student_went_to_especial(
    row: dict[str, Any],
    *,
    min_score: float = 70.0,
) -> bool:
    pending_count = _count_pending_after_extraordinario(row, min_score=min_score)
    return pending_count in {1, 2}


def _student_has_failed_module(
    row: dict[str, Any],
    *,
    min_score: float = 70.0,
) -> bool:
    cycle = _detect_cycle(row)

    if _normalize_key(cycle) != "SEGUNDO CICLO":
        return False

    for module_number in range(1, 6):
        module_name = _normalize_text(row.get(f"MOD{module_number}_NOMBRE"))
        module_cf = _safe_float(row.get(f"MOD{module_number}_CF"))

        if not module_name and module_cf is None:
            continue

        if module_cf is not None and module_cf < min_score:
            return True

    return False


def _student_failed_after_special(
    row: dict[str, Any],
    *,
    min_score: float = 70.0,
) -> bool:
    cycle = _detect_cycle(row)
    subject_catalog = _subject_catalog_for_cycle(cycle)

    return any(
        _subject_status(row, subject_code, min_score=min_score)["failed_after_special"]
        for subject_code in subject_catalog
    )


def _is_promoted_final(
    row: dict[str, Any],
    *,
    min_score: float = 70.0,
) -> bool:
    if _student_has_failed_module(row, min_score=min_score):
        return False

    cycle = _detect_cycle(row)
    subject_catalog = _subject_catalog_for_cycle(cycle)

    for subject_code in subject_catalog:
        subject_result = _subject_status(row, subject_code, min_score=min_score)

        if not subject_result["promoted"]:
            return False

    return True


def _is_reprobado_final(
    row: dict[str, Any],
    *,
    min_score: float = 70.0,
) -> bool:
    if _student_has_failed_module(row, min_score=min_score):
        return True

    if _student_failed_after_special(row, min_score=min_score):
        return True

    pending_after_extraordinario = _count_pending_after_extraordinario(
        row,
        min_score=min_score,
    )

    return pending_after_extraordinario >= 3


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

    return {
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
        sex_label = _normalize_sex_label(row.get("SEXO"))
        status = row.get("ESTADO")

        is_active = _is_active_status(status)
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

            promoted_final = _is_promoted_final(
                row,
                min_score=min_score,
            )

            no_promoted = _is_reprobado_final(
                row,
                min_score=min_score,
            )

            promoted_without_completivo = (
                promoted_final
                and not went_completivo
                and not went_extraordinario
                and not went_especial
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

    return {
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
                "Los módulos formativos con calificación menor de 70 se consideran no promovidos del grado técnico.",
                "Después de extraordinario, una o dos asignaturas pendientes pasan a especial; tres o más implican reprobación del grado.",
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