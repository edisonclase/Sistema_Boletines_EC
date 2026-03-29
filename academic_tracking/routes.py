"""
routes.py

Rutas del módulo academic_tracking.
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

# Ajusta aquí los logos por centro cuando lo necesites.
DEFAULT_INSTITUTION_LOGOS = [
    {
        "src": "/assets/logo.jpg",
        "alt": "Logo del centro educativo",
    },
    {
        "src": "/assets/minerd.png",
        "alt": "Logo institucional",
    },
]


def _parse_min_approval_score(
    raw_value: Optional[str],
    default: float = 70.0,
) -> float:
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
    student_status: Optional[str] = None,
    min_approval_score: float = 70.0,
    grade_name: Optional[str] = None,
    section_name: Optional[str] = None,
):
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
        grade_name=grade_name,
        section_name=section_name,
        period_code=period_code,
        subject_code=subject_code,
        student_status=student_status,
        min_score=min_approval_score,
        teacher_assignments=teacher_assignments,
    )

    dashboard_data["theme"] = {
        "primary_color": "#1f8f4a",
        "primary_dark": "#0b3d24",
        "primary_soft": "#eaf5ef",
    }

    dashboard_data["institution"] = {
        "name": "Centro Educativo Ejemplo",
        "school_year": school_year or "2025-2026",
        "ciclo": ciclo or "Vista general",
        "logos": DEFAULT_INSTITUTION_LOGOS,
        "favicon": "/assets/interface_logo.png",
    }

    return dashboard_data


@router.get("/", response_class=HTMLResponse, name="academic_tracking_dashboard")
def dashboard(
    request: Request,
    center_id: Optional[str] = Query(default=None),
    school_year: Optional[str] = Query(default=None),
    ciclo: Optional[str] = Query(default=None),
    curso: Optional[str] = Query(default=None),
    grado: Optional[str] = Query(default=None),
    seccion: Optional[str] = Query(default=None),
    periodo: Optional[str] = Query(default=None),
    asignatura: Optional[str] = Query(default=None),
    estado: Optional[str] = Query(default=None),
    min_approval_score: Optional[str] = Query(default=None),
):
    min_score = _parse_min_approval_score(min_approval_score, default=70.0)

    dashboard_payload = _build_dashboard_payload(
        center_id=center_id,
        school_year=school_year,
        ciclo=ciclo,
        course_name=curso,
        grade_name=grado,
        section_name=seccion,
        period_code=periodo,
        subject_code=asignatura,
        student_status=estado,
        min_approval_score=min_score,
    )

    return templates.TemplateResponse(
        "academic_tracking_dashboard.html",
        {
            "request": request,
            "dashboard": dashboard_payload,
            "view_mode": "general",
        },
    )


@router.get("/primer-ciclo", response_class=HTMLResponse, name="academic_tracking_primer_ciclo")
def primer_ciclo_dashboard(
    request: Request,
    center_id: Optional[str] = Query(default=None),
    school_year: Optional[str] = Query(default=None),
    curso: Optional[str] = Query(default=None),
    grado: Optional[str] = Query(default=None),
    seccion: Optional[str] = Query(default=None),
    periodo: Optional[str] = Query(default=None),
    asignatura: Optional[str] = Query(default=None),
    estado: Optional[str] = Query(default=None),
    min_approval_score: Optional[str] = Query(default=None),
):
    min_score = _parse_min_approval_score(min_approval_score, default=70.0)

    dashboard_payload = _build_dashboard_payload(
        center_id=center_id,
        school_year=school_year,
        ciclo="Primer Ciclo",
        course_name=curso,
        grade_name=grado,
        section_name=seccion,
        period_code=periodo,
        subject_code=asignatura,
        student_status=estado,
        min_approval_score=min_score,
    )

    return templates.TemplateResponse(
        "academic_tracking_dashboard.html",
        {
            "request": request,
            "dashboard": dashboard_payload,
            "view_mode": "primer_ciclo",
        },
    )


@router.get("/segundo-ciclo", response_class=HTMLResponse, name="academic_tracking_segundo_ciclo")
def segundo_ciclo_dashboard(
    request: Request,
    center_id: Optional[str] = Query(default=None),
    school_year: Optional[str] = Query(default=None),
    curso: Optional[str] = Query(default=None),
    grado: Optional[str] = Query(default=None),
    seccion: Optional[str] = Query(default=None),
    periodo: Optional[str] = Query(default=None),
    asignatura: Optional[str] = Query(default=None),
    estado: Optional[str] = Query(default=None),
    min_approval_score: Optional[str] = Query(default=None),
):
    min_score = _parse_min_approval_score(min_approval_score, default=70.0)

    dashboard_payload = _build_dashboard_payload(
        center_id=center_id,
        school_year=school_year,
        ciclo="Segundo Ciclo",
        course_name=curso,
        grade_name=grado,
        section_name=seccion,
        period_code=periodo,
        subject_code=asignatura,
        student_status=estado,
        min_approval_score=min_score,
    )

    return templates.TemplateResponse(
        "academic_tracking_dashboard.html",
        {
            "request": request,
            "dashboard": dashboard_payload,
            "view_mode": "segundo_ciclo",
        },
    )


@router.get("/data", name="academic_tracking_dashboard_data")
def dashboard_data(
    center_id: Optional[str] = Query(default=None),
    school_year: Optional[str] = Query(default=None),
    ciclo: Optional[str] = Query(default=None),
    curso: Optional[str] = Query(default=None),
    grado: Optional[str] = Query(default=None),
    seccion: Optional[str] = Query(default=None),
    periodo: Optional[str] = Query(default=None),
    asignatura: Optional[str] = Query(default=None),
    estado: Optional[str] = Query(default=None),
    min_approval_score: Optional[str] = Query(default=None),
):
    min_score = _parse_min_approval_score(min_approval_score, default=70.0)

    dashboard_payload = _build_dashboard_payload(
        center_id=center_id,
        school_year=school_year,
        ciclo=ciclo,
        course_name=curso,
        grade_name=grado,
        section_name=seccion,
        period_code=periodo,
        subject_code=asignatura,
        student_status=estado,
        min_approval_score=min_score,
    )

    return dashboard_payload


@router.get("/health", name="academic_tracking_health")
def healthcheck():
    return {
        "module": "academic_tracking",
        "status": "ok",
        "message": "Academic tracking module is running.",
    }