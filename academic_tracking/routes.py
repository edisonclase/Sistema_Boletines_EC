"""
routes.py

Rutas del módulo academic_tracking.

Objetivos:
- Exponer una vista nueva e independiente para coordinadores
- No tocar rutas de boletines ni PDF
- Permitir filtros por centro, ciclo, curso, período y asignatura
- Soportar carga futura desde Google Sheets, BD o servicios propios

Notas:
- Este archivo asume integración con Flask
- La carga real de datos del sheet se deja desacoplada en funciones helper
- Si luego conectamos con BD o servicios internos, solo cambiamos la fuente
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from flask import Blueprint, jsonify, render_template, request

from .services.tracking_service import build_tracking_dashboard_data
from .services.data_loader_service import (
    load_academic_rows_from_source,
    load_teacher_assignments_from_source,
)


academic_tracking_bp = Blueprint(
    "academic_tracking",
    __name__,
    template_folder="templates",
    static_folder="static",
    url_prefix="/academic-tracking",
)


# =========================
# Helpers internos
# =========================

def _get_request_arg(name: str, default: Optional[str] = None) -> Optional[str]:
    """
    Lee parámetros GET y limpia espacios.
    """
    value = request.args.get(name, default)
    if value is None:
        return default

    value = str(value).strip()
    return value if value else default


def _get_current_center_id() -> Optional[Any]:
    return _get_request_arg("center_id")


def _get_current_school_year() -> Optional[str]:
    return _get_request_arg("school_year")


def _get_current_ciclo() -> Optional[str]:
    return _get_request_arg("ciclo")


def _get_current_course_name() -> Optional[str]:
    return _get_request_arg("curso")


def _get_current_period_code() -> Optional[str]:
    return _get_request_arg("periodo")


def _get_current_subject_code() -> Optional[str]:
    return _get_request_arg("asignatura")


def _get_min_approval_score(default: float = 70.0) -> float:
    raw_value = _get_request_arg("min_approval_score")
    if raw_value is None:
        return default

    try:
        return float(raw_value)
    except ValueError:
        return default


def _build_dashboard_response(as_json: bool = False):
    """
    Construye la respuesta principal del dashboard.
    """
    center_id = _get_current_center_id()
    school_year = _get_current_school_year()
    ciclo = _get_current_ciclo()
    course_name = _get_current_course_name()
    period_code = _get_current_period_code()
    subject_code = _get_current_subject_code()
    min_approval_score = _get_min_approval_score()

    # 🔹 Carga desacoplada (YA CONECTADA A SERVICE)
    rows = load_academic_rows_from_source(
        center_id=center_id,
        school_year=school_year,
        ciclo=ciclo,
    )

    teacher_assignments = load_teacher_assignments_from_source(
        center_id=center_id,
        school_year=school_year,
        ciclo=ciclo,
    )

    dashboard_data = build_tracking_dashboard_data(
        rows=rows,
        center_id=center_id,
        school_year=school_year,
        ciclo=ciclo,
        course_name=course_name,
        period_code=period_code,
        subject_code=subject_code,
        min_score=min_approval_score,
        teacher_assignments=teacher_assignments,
    )

    if as_json:
        return jsonify(dashboard_data)

    return render_template(
        "academic_tracking_dashboard.html",
        dashboard=dashboard_data,
    )


# =========================
# Rutas públicas del módulo
# =========================

@academic_tracking_bp.route("/", methods=["GET"])
def dashboard():
    """
    Vista principal HTML del dashboard académico.
    """
    return _build_dashboard_response(as_json=False)


@academic_tracking_bp.route("/data", methods=["GET"])
def dashboard_data():
    """
    Salida JSON del dashboard.

    Útil para:
    - pruebas
    - depuración
    - futura integración AJAX
    - validación de estructura antes de pulir la interfaz
    """
    return _build_dashboard_response(as_json=True)


@academic_tracking_bp.route("/health", methods=["GET"])
def healthcheck():
    """
    Ruta simple para validar que el módulo está vivo.
    """
    return jsonify(
        {
            "module": "academic_tracking",
            "status": "ok",
            "message": "Academic tracking module is running.",
        }
    )