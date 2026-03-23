"""
routes.py

Rutas del módulo academic_tracking.

Objetivos:
- Exponer una vista nueva e independiente para coordinadores.
- No tocar rutas de boletines ni PDF.
- Permitir filtros por centro, ciclo, curso, período y asignatura.
- Soportar carga futura desde Google Sheets, BD o servicios propios.

Notas:
- Este archivo asume integración con FastAPI.
- La carga real de datos del sheet se deja desacoplada en services.
- Si luego conectamos con BD o servicios internos, solo cambiamos la fuente.
"""

from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from .services.data_loader_service import (
    load_academic_rows_from_source,
    load_teacher_assignments_from_source,
)
from .services.tracking_service import build_tracking_dashboard_data


router = APIRouter(
    prefix="/academic-tracking",
    tags=["academic_tracking"],
)

templates = Jinja2Templates(directory="academic_tracking/templates")


# =========================
# Helpers internos
# =========================
def _parse_min_approval_score(
    raw_value: Optional[str],
    default: float = 70.0,
) -> float:
    """
    Convierte el valor del query param a float de manera segura.
    """
    if raw_value is None:
        return default

    raw_value = str(raw_value).strip()
    if not raw_value:
        return default

    try:
        return float(raw_value)
    except ValueError:
        return default


def _build_dashboard_payload(
    center_id: Optional[Any] = None,
    school_year: Optional[str] = None,
    ciclo: Optional[str] = None,
    course_name: Optional[str] = None,
    period_code: Optional[str] = None,
    subject_code: Optional[str] = None,
    min_approval_score: float = 70.0,
) -> dict[str, Any]:
    """
    Construye la data unificada del dashboard.
    """
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

    # Tema visual base del sistema.
    # Más adelante podrá venir desde la configuración del centro.
    dashboard_data["theme"] = {
        "primary_color": "#1f6f43",
        "primary_dark": "#185735",
        "primary_soft": "#eaf5ef",
    }

    return dashboard_data


# =========================
# Rutas públicas del módulo
# =========================
@router.get("/", response_class=HTMLResponse)
def dashboard(
    request: Request,
    center_id: Optional[str] = Query(default=None),
    school_year: Optional[str] = Query(default=None),
    ciclo: Optional[str] = Query(default=None),
    curso: Optional[str] = Query(default=None),
    periodo: Optional[str] = Query(default=None),
    asignatura: Optional[str] = Query(default=None),
    min_approval_score: Optional[str] = Query(default=None),
):
    """
    Vista principal HTML del dashboard académico.
    """
    min_score = _parse_min_approval_score(
        min_approval_score,
        default=70.0,
    )

    dashboard_payload = _build_dashboard_payload(
        center_id=center_id,
        school_year=school_year,
        ciclo=ciclo,
        course_name=curso,
        period_code=periodo,
        subject_code=asignatura,
        min_approval_score=min_score,
    )

    return templates.TemplateResponse(
        "academic_tracking_dashboard.html",
        {
            "request": request,
            "dashboard": dashboard_payload,
        },
    )


@router.get("/data")
def dashboard_data(
    center_id: Optional[str] = Query(default=None),
    school_year: Optional[str] = Query(default=None),
    ciclo: Optional[str] = Query(default=None),
    curso: Optional[str] = Query(default=None),
    periodo: Optional[str] = Query(default=None),
    asignatura: Optional[str] = Query(default=None),
    min_approval_score: Optional[str] = Query(default=None),
):
    """
    Salida JSON del dashboard.

    Útil para:
    - pruebas
    - depuración
    - futura integración AJAX
    - validación de estructura antes de pulir la interfaz
    """
    min_score = _parse_min_approval_score(
        min_approval_score,
        default=70.0,
    )

    dashboard_payload = _build_dashboard_payload(
        center_id=center_id,
        school_year=school_year,
        ciclo=ciclo,
        course_name=curso,
        period_code=periodo,
        subject_code=asignatura,
        min_approval_score=min_score,
    )

    return dashboard_payload


@router.get("/health")
def healthcheck():
    """
    Ruta simple para validar que el módulo está vivo.
    """
    return {
        "module": "academic_tracking",
        "status": "ok",
        "message": "Academic tracking module is running.",
    }