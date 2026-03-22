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
    """
    Obtiene center_id desde query string.

    Nota:
    Hoy puede venir por URL.
    Más adelante puede venir por sesión, usuario autenticado o centro activo.
    """
    return _get_request_arg("center_id")


def _get_current_school_year() -> Optional[str]:
    """
    Obtiene el año escolar activo.
    """
    return _get_request_arg("school_year")


def _get_current_ciclo() -> Optional[str]:
    """
    Obtiene el ciclo filtrado.
    """
    return _get_request_arg("ciclo")


def _get_current_course_name() -> Optional[str]:
    """
    Obtiene el curso filtrado.
    """
    return _get_request_arg("curso")


def _get_current_period_code() -> Optional[str]:
    """
    Obtiene el período filtrado.
    """
    return _get_request_arg("periodo")


def _get_current_subject_code() -> Optional[str]:
    """
    Obtiene la asignatura filtrada.
    """
    return _get_request_arg("asignatura")


def _get_min_approval_score(default: float = 70.0) -> float:
    """
    Obtiene el mínimo de aprobación desde query string.
    """
    raw_value = _get_request_arg("min_approval_score")
    if raw_value is None:
        return default

    try:
        return float(raw_value)
    except ValueError:
        return default


def _load_academic_rows() -> List[Dict[str, Any]]:
    """
    Carga la data académica base.

    IMPORTANTE:
    Este helper es placeholder intencional.

    Aquí NO estamos tocando la lógica existente de boletines.
    Más adelante, este punto debe conectarse a la misma fuente actual:
    - import desde Google Sheets
    - servicio interno existente
    - capa de datos compartida del proyecto

    Por ahora devuelve una lista vacía para no romper la estructura.
    """
    return []


def _load_teacher_assignments() -> List[Dict[str, Any]]:
    """
    Carga la fuente auxiliar de docente_asignatura.

    Esta fuente debe ser independiente del import principal de notas,
    para no romper la estructura actual de Google Sheets.

    Más adelante puede venir de:
    - una hoja auxiliar Google Sheets
    - una tabla en BD
    - una configuración administrativa en el sistema
    """
    return []


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

    rows = _load_academic_rows()
    teacher_assignments = _load_teacher_assignments()

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