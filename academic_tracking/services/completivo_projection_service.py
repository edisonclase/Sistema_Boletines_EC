"""
completivo_projection_service.py

Servicio preventivo para identificar estudiantes con tendencia a ir a completivo.

Regla:
- Usa las columnas PC1, PC2, PC3 y PC4 de cada asignatura.
- Solo toma en cuenta períodos publicados, es decir, valores mayores que 0.
- Si el promedio actual de los períodos publicados es menor a 70,
  el estudiante queda proyectado a completivo en esa asignatura.
- Calcula puntos faltantes para llegar a 70.
- Clasifica el nivel de riesgo:
  - bajo: faltan menos de 5 puntos
  - medio: faltan de 5 a 9.99 puntos
  - alto: faltan 10 puntos o más
"""

from __future__ import annotations

import math
from typing import Any, Optional

from .parsing_service import normalize_text, safe_float


SUBJECTS = {
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

PERIOD_COLUMNS = ["PC1", "PC2", "PC3", "PC4"]

MIN_PASS_SCORE = 70.0

RISK_LEVEL_OPTIONS = [
    {"value": "", "label": "Todos los riesgos"},
    {"value": "alto", "label": "Riesgo alto"},
    {"value": "medio", "label": "Riesgo medio"},
    {"value": "bajo", "label": "Riesgo bajo"},
]

PROJECTION_STRENGTH_OPTIONS = [
    {"value": "", "label": "Todas las tendencias"},
    {"value": "preliminar", "label": "Tendencia preliminar"},
    {"value": "fuerte", "label": "Tendencia fuerte"},
    {"value": "final", "label": "Situación final"},
]

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


def _get_student_status(row: dict[str, Any]) -> str:
    status = normalize_text(
        _get_row_value_flexible(
            row,
            ["ESTADO", "STATUS", "CONDICION", "CONDICIÓN"],
        )
    )

    return status.upper().strip()


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


def _get_course_name(row: dict[str, Any]) -> str:
    return normalize_text(row.get("CURSO"))


def _has_real_student_identity(row: dict[str, Any]) -> bool:
    student_id = _get_student_id(row)
    student_name = _get_student_name(row)
    course_name = _get_course_name(row)

    return bool(student_id or student_name) and bool(course_name)


def _get_score(row: dict[str, Any], column_name: str) -> Optional[float]:
    return safe_float(row.get(column_name))


def _is_published_score(value: Optional[float]) -> bool:
    return value is not None and value > 0


def _calculate_average(values: list[float]) -> Optional[float]:
    if not values:
        return None

    return round(sum(values) / len(values), 2)


def _build_risk_payload(
    current_average: float,
    published_periods_count: int,
) -> dict[str, Any]:
    points_needed = round(MIN_PASS_SCORE - current_average, 2)

    if points_needed >= 10:
        risk_level = "alto"
        risk_label = "Riesgo alto"
    elif points_needed >= 5:
        risk_level = "medio"
        risk_label = "Riesgo medio"
    else:
        risk_level = "bajo"
        risk_label = "Riesgo bajo"

    if published_periods_count <= 2:
        projection_strength = "preliminar"
        projection_strength_label = "Tendencia preliminar"
    elif published_periods_count == 3:
        projection_strength = "fuerte"
        projection_strength_label = "Tendencia fuerte"
    else:
        projection_strength = "final"
        projection_strength_label = "Situación final"

    return {
        "points_needed": points_needed,
        "risk_level": risk_level,
        "risk_label": risk_label,
        "projection_strength": projection_strength,
        "projection_strength_label": projection_strength_label,
    }


def analyze_subject_projection(
    row: dict[str, Any],
    subject_code: str,
) -> Optional[dict[str, Any]]:
    subject_name = SUBJECTS.get(subject_code, subject_code)

    period_scores: dict[str, Optional[float]] = {}
    published_scores: list[float] = []

    for period_column in PERIOD_COLUMNS:
        column_name = f"{subject_code}_{period_column}"
        score = _get_score(row, column_name)

        period_scores[period_column] = score

        if _is_published_score(score):
            published_scores.append(float(score))

    if not published_scores:
        return None

    current_average = _calculate_average(published_scores)

    if current_average is None:
        return None

    projected_to_completivo = current_average < MIN_PASS_SCORE

    if not projected_to_completivo:
        return None

    published_periods_count = len(published_scores)

    risk_payload = _build_risk_payload(
        current_average=current_average,
        published_periods_count=published_periods_count,
    )

    return {
        "subject_code": subject_code,
        "subject_name": subject_name,
        "period_scores": period_scores,
        "published_periods_count": published_periods_count,
        "current_average": current_average,
        "projected_to_completivo": projected_to_completivo,
        "status": "proyeccion_completivo",
        "status_label": "Proyectado a completivo",
        **risk_payload,
    }


def analyze_student_projection(row: dict[str, Any]) -> Optional[dict[str, Any]]:
    if not _has_real_student_identity(row):
        return None

    if not _is_active_student(row):
        return None

    student_id = _get_student_id(row)
    student_name = _get_student_name(row)
    numero = _clean_identifier_value(row.get("NUMERO"))
    course_name = _get_course_name(row)
    prof_titular = normalize_text(row.get("PROF_TITULAR"))

    projected_subjects: list[dict[str, Any]] = []

    for subject_code in SUBJECTS:
        subject_projection = analyze_subject_projection(
            row=row,
            subject_code=subject_code,
        )

        if subject_projection:
            projected_subjects.append(subject_projection)

    if not projected_subjects:
        return None

    lowest_average = min(
        item["current_average"]
        for item in projected_subjects
        if item.get("current_average") is not None
    )

    highest_points_needed = max(
        item["points_needed"]
        for item in projected_subjects
        if item.get("points_needed") is not None
    )

    risk_priority = {
        "alto": 3,
        "medio": 2,
        "bajo": 1,
    }

    highest_risk_subject = max(
        projected_subjects,
        key=lambda item: risk_priority.get(item.get("risk_level"), 0),
    )

    strongest_projection_subject = max(
        projected_subjects,
        key=lambda item: int(item.get("published_periods_count", 0)),
    )

    return {
        "student_id": student_id,
        "student_name": student_name,
        "numero": numero,
        "course_name": course_name,
        "prof_titular": prof_titular,
        "projected_subjects": projected_subjects,
        "projected_subjects_count": len(projected_subjects),
        "lowest_average": lowest_average,
        "highest_points_needed": highest_points_needed,
        "highest_risk_level": highest_risk_subject.get("risk_level"),
        "highest_risk_label": highest_risk_subject.get("risk_label"),
        "projection_strength": strongest_projection_subject.get("projection_strength"),
        "projection_strength_label": strongest_projection_subject.get("projection_strength_label"),
        "status": "proyeccion_completivo",
        "status_label": "Proyectado a completivo",
    }


def _student_matches_filters(
    student: dict[str, Any],
    curso: Optional[str] = None,
    asignatura: Optional[str] = None,
    riesgo: Optional[str] = None,
    tendencia: Optional[str] = None,
) -> bool:
    normalized_course = normalize_text(curso)
    normalized_subject = normalize_text(asignatura).upper()
    normalized_risk = normalize_text(riesgo).lower()
    normalized_strength = normalize_text(tendencia).lower()

    if normalized_course:
        if normalize_text(student.get("course_name")) != normalized_course:
            return False

    projected_subjects = student.get("projected_subjects", [])

    if normalized_subject:
        projected_subjects = [
            item
            for item in projected_subjects
            if normalize_text(item.get("subject_code")).upper() == normalized_subject
        ]

    if normalized_risk:
        projected_subjects = [
            item
            for item in projected_subjects
            if normalize_text(item.get("risk_level")).lower() == normalized_risk
        ]

    if normalized_strength:
        projected_subjects = [
            item
            for item in projected_subjects
            if normalize_text(item.get("projection_strength")).lower() == normalized_strength
        ]

    return bool(projected_subjects)


def _filter_student_subjects(
    student: dict[str, Any],
    asignatura: Optional[str] = None,
    riesgo: Optional[str] = None,
    tendencia: Optional[str] = None,
) -> dict[str, Any]:
    normalized_subject = normalize_text(asignatura).upper()
    normalized_risk = normalize_text(riesgo).lower()
    normalized_strength = normalize_text(tendencia).lower()

    filtered_subjects = list(student.get("projected_subjects", []))

    if normalized_subject:
        filtered_subjects = [
            item
            for item in filtered_subjects
            if normalize_text(item.get("subject_code")).upper() == normalized_subject
        ]

    if normalized_risk:
        filtered_subjects = [
            item
            for item in filtered_subjects
            if normalize_text(item.get("risk_level")).lower() == normalized_risk
        ]

    if normalized_strength:
        filtered_subjects = [
            item
            for item in filtered_subjects
            if normalize_text(item.get("projection_strength")).lower() == normalized_strength
        ]

    copied = dict(student)
    copied["projected_subjects"] = filtered_subjects
    copied["projected_subjects_count"] = len(filtered_subjects)

    if filtered_subjects:
        copied["lowest_average"] = min(
            item["current_average"]
            for item in filtered_subjects
            if item.get("current_average") is not None
        )

        copied["highest_points_needed"] = max(
            item["points_needed"]
            for item in filtered_subjects
            if item.get("points_needed") is not None
        )

        risk_priority = {
            "alto": 3,
            "medio": 2,
            "bajo": 1,
        }

        highest_risk_subject = max(
            filtered_subjects,
            key=lambda item: risk_priority.get(item.get("risk_level"), 0),
        )

        strongest_projection_subject = max(
            filtered_subjects,
            key=lambda item: int(item.get("published_periods_count", 0)),
        )

        copied["highest_risk_level"] = highest_risk_subject.get("risk_level")
        copied["highest_risk_label"] = highest_risk_subject.get("risk_label")
        copied["projection_strength"] = strongest_projection_subject.get("projection_strength")
        copied["projection_strength_label"] = strongest_projection_subject.get("projection_strength_label")
    else:
        copied["lowest_average"] = None
        copied["highest_points_needed"] = None
        copied["highest_risk_level"] = None
        copied["highest_risk_label"] = None
        copied["projection_strength"] = None
        copied["projection_strength_label"] = None

    return copied


def build_completivo_projection_report(
    rows: list[dict[str, Any]],
    curso: Optional[str] = None,
    asignatura: Optional[str] = None,
    riesgo: Optional[str] = None,
    tendencia: Optional[str] = None,
) -> dict[str, Any]:
    analyzed_students: list[dict[str, Any]] = []

    for row in rows:
        student_projection = analyze_student_projection(row)

        if not student_projection:
            continue

        if not _student_matches_filters(
            student=student_projection,
            curso=curso,
            asignatura=asignatura,
            riesgo=riesgo,
            tendencia=tendencia,
        ):
            continue

        student_projection = _filter_student_subjects(
            student=student_projection,
            asignatura=asignatura,
            riesgo=riesgo,
            tendencia=tendencia,
        )

        if student_projection.get("projected_subjects"):
            analyzed_students.append(student_projection)

    courses = sorted(
        {
            normalize_text(item.get("course_name"))
            for item in analyzed_students
            if normalize_text(item.get("course_name"))
        }
    )

    subjects_with_cases = sorted(
        {
            subject.get("subject_name")
            for student in analyzed_students
            for subject in student.get("projected_subjects", [])
            if subject.get("subject_name")
        }
    )

    total_subject_cases = sum(
        int(student.get("projected_subjects_count", 0))
        for student in analyzed_students
    )

    risk_counts = {
        "alto": 0,
        "medio": 0,
        "bajo": 0,
    }

    strength_counts = {
        "preliminar": 0,
        "fuerte": 0,
        "final": 0,
    }

    for student in analyzed_students:
        for subject in student.get("projected_subjects", []):
            risk_level = normalize_text(subject.get("risk_level")).lower()
            projection_strength = normalize_text(subject.get("projection_strength")).lower()

            if risk_level in risk_counts:
                risk_counts[risk_level] += 1

            if projection_strength in strength_counts:
                strength_counts[projection_strength] += 1

    return {
        "summary": {
            "students_projected": len(analyzed_students),
            "subject_cases": total_subject_cases,
            "courses_with_cases": len(courses),
            "subjects_with_cases": len(subjects_with_cases),
            "risk_counts": risk_counts,
            "strength_counts": strength_counts,
        },
        "students": analyzed_students,
        "courses": courses,
        "subjects_with_cases": subjects_with_cases,
        "subjects_catalog": [
            {"value": code, "label": name}
            for code, name in SUBJECTS.items()
        ],
        "risk_level_options": RISK_LEVEL_OPTIONS,
        "projection_strength_options": PROJECTION_STRENGTH_OPTIONS,
    }