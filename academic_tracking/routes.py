"""
routes.py

Rutas del módulo academic_tracking.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

from fastapi import APIRouter, Query, Request
from fastapi.responses import HTMLResponse, Response
from fastapi.templating import Jinja2Templates

from .services.data_loader_service import (
    load_academic_rows_from_source,
    load_teacher_assignments_from_source,
)
from .services.tracking_service import build_tracking_dashboard_data
from .services.final_status_service import build_final_status_report
from .services.completivo_projection_service import build_completivo_projection_report
from app.core.settings import settings


router = APIRouter(
    prefix="/academic-tracking",
    tags=["academic_tracking"],
)

templates = Jinja2Templates(directory="academic_tracking/templates")


def _parse_min_approval_score(raw_value: Optional[str], default: float = 70.0) -> float:
    if raw_value is None:
        return default

    raw_value = str(raw_value).strip()
    if not raw_value:
        return default

    try:
        return float(raw_value)
    except ValueError:
        return default


def _resolve_institution_name() -> str:
    return str(
        getattr(settings, "institution_name", "")
        or "Centro Educativo Ejemplo"
    ).strip()


def _resolve_school_year(fallback: Optional[str] = None) -> str:
    configured = str(getattr(settings, "school_year", "") or "").strip()
    if configured:
        return configured

    return str(fallback or "2025-2026").strip()


def _resolve_institution_logos() -> list[dict[str, str]]:
    logos: list[dict[str, str]] = []

    def to_asset_url(path: str) -> str:
        if not path:
            return ""

        filename = path.split("/")[-1]
        return f"/assets/{filename}"

    institution_logo = getattr(settings, "institution_logo", "")

    if institution_logo:
        logos.append(
            {
                "src": to_asset_url(institution_logo),
                "alt": "Logo del centro educativo",
            }
        )

    return logos


def _project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _render_pdf_bytes_from_html(html: str, base_url: Optional[str] = None) -> bytes:
    engine = str(getattr(settings, "pdf_engine", "") or "").strip().lower()

    if engine == "weasyprint":
        return _render_pdf_bytes_weasyprint(html, base_url=base_url)

    if engine == "wkhtmltopdf":
        return _render_pdf_bytes_pdfkit(html)

    try:
        return _render_pdf_bytes_pdfkit(html)
    except Exception as exc:
        print(
            f"[academic_tracking PDF] pdfkit falló. Se intentará WeasyPrint. Error: {exc}",
            flush=True,
        )
        return _render_pdf_bytes_weasyprint(html, base_url=base_url)


def _render_pdf_bytes_pdfkit(html: str) -> bytes:
    import pdfkit

    config = None
    wkhtmltopdf_path = str(getattr(settings, "wkhtmltopdf_path", "") or "").strip()

    if wkhtmltopdf_path:
        config = pdfkit.configuration(wkhtmltopdf=wkhtmltopdf_path)

    options = {
        "encoding": "UTF-8",
        "quiet": "",
        "enable-local-file-access": "",
        "page-size": "Letter",
        "orientation": "Landscape",
        "margin-top": "0.6cm",
        "margin-right": "0.6cm",
        "margin-bottom": "0.6cm",
        "margin-left": "0.6cm",
        "print-media-type": "",
        "disable-smart-shrinking": "",
    }

    return pdfkit.from_string(
        html,
        False,
        options=options,
        configuration=config,
    )


def _render_pdf_bytes_weasyprint(html: str, base_url: Optional[str] = None) -> bytes:
    from weasyprint import HTML

    return HTML(
        string=html,
        base_url=base_url or str(_project_root()),
    ).write_pdf()


def _render_template_to_html(
    template_name: str,
    request: Request,
    dashboard_payload: dict[str, Any],
) -> str:
    template_response = templates.TemplateResponse(
        template_name,
        {
            "request": request,
            "dashboard": dashboard_payload,
        },
    )

    return template_response.body.decode("utf-8")


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
        "name": _resolve_institution_name(),
        "school_year": _resolve_school_year(school_year),
        "ciclo": ciclo or "Vista general",
        "logos": _resolve_institution_logos(),
        "favicon": "/assets/interface_logo.png",
    }

    return dashboard_data


def _normalize_text(value: Optional[Any]) -> str:
    return str(value or "").strip()


def _split_course_name(course_name: str) -> tuple[str, str]:
    text = _normalize_text(course_name)

    if not text:
        return ("", "")

    parts = text.split(maxsplit=1)

    if len(parts) == 2:
        return (parts[0].strip(), parts[1].strip())

    return (text, "")


def _student_matches_final_filters(
    student: dict[str, Any],
    situacion: Optional[str] = None,
    curso: Optional[str] = None,
    grado: Optional[str] = None,
    seccion: Optional[str] = None,
) -> bool:
    normalized_situacion = _normalize_text(situacion)
    normalized_curso = _normalize_text(curso)
    normalized_grado = _normalize_text(grado)
    normalized_seccion = _normalize_text(seccion)

    course_name = _normalize_text(student.get("course_name"))
    raw_grade, raw_section = _split_course_name(course_name)

    if normalized_situacion:
        if _normalize_text(student.get("final_status")) != normalized_situacion:
            return False

    if normalized_curso:
        if course_name != normalized_curso:
            return False

    if normalized_grado:
        if raw_grade != normalized_grado:
            return False

    if normalized_seccion:
        if raw_section != normalized_seccion:
            return False

    return True


def _filter_final_status_report(
    report: dict[str, Any],
    situacion: Optional[str] = None,
    curso: Optional[str] = None,
    grado: Optional[str] = None,
    seccion: Optional[str] = None,
) -> dict[str, Any]:
    filtered_students = [
        student
        for student in report.get("students", [])
        if _student_matches_final_filters(
            student=student,
            situacion=situacion,
            curso=curso,
            grado=grado,
            seccion=seccion,
        )
    ]

    promoted_students = [
        item for item in filtered_students if item.get("final_status") == "promovido"
    ]

    completivo_students = [
        item for item in filtered_students if item.get("final_status") == "completivo"
    ]

    extraordinario_students = [
        item for item in filtered_students if item.get("final_status") == "extraordinario"
    ]

    especial_students = [
        item for item in filtered_students if item.get("final_status") == "especial"
    ]

    module_special_students = [
        item for item in filtered_students if item.get("final_status") == "modulo_especial"
    ]

    sin_datos_students = [
        item for item in filtered_students if item.get("final_status") == "sin_datos"
    ]

    filtered_report = dict(report)

    filtered_report["students"] = filtered_students
    filtered_report["promoted_students"] = promoted_students
    filtered_report["completivo_students"] = completivo_students
    filtered_report["extraordinario_students"] = extraordinario_students
    filtered_report["especial_students"] = especial_students
    filtered_report["module_special_students"] = module_special_students
    filtered_report["sin_datos_students"] = sin_datos_students

    original_summary = report.get("summary", {})

    filtered_report["summary"] = {
        **original_summary,
        "filtered_total_students": len(filtered_students),
        "filtered_promoted": len(promoted_students),
        "filtered_completivo": len(completivo_students),
        "filtered_extraordinario": len(extraordinario_students),
        "filtered_especial": len(especial_students),
        "filtered_modulo_especial": len(module_special_students),
        "filtered_sin_datos": len(sin_datos_students),
    }

    return filtered_report


def _build_final_status_catalog(report: dict[str, Any]) -> dict[str, Any]:
    courses_map: dict[str, dict[str, str]] = {}
    grades_map: dict[str, str] = {}
    sections_map: dict[str, str] = {}
    sections_by_grade: dict[str, list[str]] = {}

    for student in report.get("students", []):
        course_name = _normalize_text(student.get("course_name"))
        if not course_name:
            continue

        raw_grade, raw_section = _split_course_name(course_name)

        courses_map[course_name] = {
            "value": course_name,
            "label": course_name,
        }

        if raw_grade:
            grades_map[raw_grade] = raw_grade

        if raw_section:
            sections_map[raw_section] = raw_section
            sections_by_grade.setdefault(raw_grade, [])
            if raw_section not in sections_by_grade[raw_grade]:
                sections_by_grade[raw_grade].append(raw_section)

    return {
        "courses_catalog": sorted(courses_map.values(), key=lambda item: item["label"]),
        "grades_catalog": [
            {"value": value, "label": label}
            for value, label in sorted(grades_map.items(), key=lambda item: item[0])
        ],
        "sections_catalog": [
            {"value": value, "label": label}
            for value, label in sorted(sections_map.items(), key=lambda item: item[0])
        ],
        "sections_by_grade": {
            grade: sorted(section_list)
            for grade, section_list in sections_by_grade.items()
        },
        "situation_options": [
            {"value": "", "label": "Resumen general"},
            {"value": "promovido", "label": "Promovidos"},
            {"value": "completivo", "label": "Completivo"},
            {"value": "extraordinario", "label": "Extraordinario"},
            {"value": "especial", "label": "Evaluación especial"},
            {"value": "modulo_especial", "label": "Módulos formativos especiales"},
            {"value": "sin_datos", "label": "Sin calificaciones finales"},
        ],
    }


@router.get(
    "/",
    response_class=HTMLResponse,
    name="academic_tracking_dashboard",
)
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
    min_score = _parse_min_approval_score(
        min_approval_score,
        default=70.0,
    )

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


@router.get(
    "/primer-ciclo",
    response_class=HTMLResponse,
    name="academic_tracking_primer_ciclo",
)
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
    min_score = _parse_min_approval_score(
        min_approval_score,
        default=70.0,
    )

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


@router.get(
    "/segundo-ciclo",
    response_class=HTMLResponse,
    name="academic_tracking_segundo_ciclo",
)
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
    min_score = _parse_min_approval_score(
        min_approval_score,
        default=70.0,
    )

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


@router.get(
    "/situacion-final",
    response_class=HTMLResponse,
    name="academic_tracking_final_status_dashboard",
)
def final_status_dashboard(
    request: Request,
    center_id: Optional[str] = Query(default=None),
    school_year: Optional[str] = Query(default=None),
    ciclo: Optional[str] = Query(default=None),
    situacion: Optional[str] = Query(default=None),
    curso: Optional[str] = Query(default=None),
    grado: Optional[str] = Query(default=None),
    seccion: Optional[str] = Query(default=None),
    print_mode: Optional[str] = Query(default=None),
):
    rows = load_academic_rows_from_source(
        center_id=center_id,
        school_year=school_year,
        ciclo=ciclo,
    )

    full_report = build_final_status_report(rows)
    catalog = _build_final_status_catalog(full_report)

    filtered_report = _filter_final_status_report(
        report=full_report,
        situacion=situacion,
        curso=curso,
        grado=grado,
        seccion=seccion,
    )

    dashboard_payload = {
        "institution": {
            "name": _resolve_institution_name(),
            "school_year": _resolve_school_year(school_year),
            "ciclo": ciclo or "Vista general",
            "logos": _resolve_institution_logos(),
            "favicon": "/assets/interface_logo.png",
        },
        "theme": {
            "primary_color": "#1f8f4a",
            "primary_dark": "#0b3d24",
            "primary_soft": "#eaf5ef",
        },
        "filters": {
            "center_id": center_id,
            "school_year": school_year,
            "ciclo": ciclo,
            "situacion": situacion,
            "curso": curso,
            "grado": grado,
            "seccion": seccion,
            "print_mode": print_mode,
        },
        "metadata": catalog,
        "report": filtered_report,
        "full_report": full_report,
        "show_students": bool(situacion or curso or grado or seccion),
        "print_mode": print_mode,
    }

    return templates.TemplateResponse(
        "final_status_dashboard.html",
        {
            "request": request,
            "dashboard": dashboard_payload,
        },
    )


@router.get(
    "/data",
    name="academic_tracking_dashboard_data",
)
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
    min_score = _parse_min_approval_score(
        min_approval_score,
        default=70.0,
    )

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


@router.get(
    "/situacion-final/data",
    name="academic_tracking_final_status_data",
)
def final_status_data(
    center_id: Optional[str] = Query(default=None),
    school_year: Optional[str] = Query(default=None),
    ciclo: Optional[str] = Query(default=None),
    situacion: Optional[str] = Query(default=None),
    curso: Optional[str] = Query(default=None),
    grado: Optional[str] = Query(default=None),
    seccion: Optional[str] = Query(default=None),
):
    rows = load_academic_rows_from_source(
        center_id=center_id,
        school_year=school_year,
        ciclo=ciclo,
    )

    full_report = build_final_status_report(rows)

    report = _filter_final_status_report(
        report=full_report,
        situacion=situacion,
        curso=curso,
        grado=grado,
        seccion=seccion,
    )

    return {
        "institution": {
            "name": _resolve_institution_name(),
            "school_year": _resolve_school_year(school_year),
            "ciclo": ciclo or "Vista general",
        },
        "filters": {
            "center_id": center_id,
            "school_year": school_year,
            "ciclo": ciclo,
            "situacion": situacion,
            "curso": curso,
            "grado": grado,
            "seccion": seccion,
        },
        "report": report,
    }


@router.get(
    "/situacion-final/reporte.pdf",
    name="academic_tracking_final_status_pdf",
)
def final_status_pdf(
    request: Request,
    center_id: Optional[str] = Query(default=None),
    school_year: Optional[str] = Query(default=None),
    ciclo: Optional[str] = Query(default=None),
    situacion: Optional[str] = Query(default=None),
    curso: Optional[str] = Query(default=None),
    grado: Optional[str] = Query(default=None),
    seccion: Optional[str] = Query(default=None),
):
    rows = load_academic_rows_from_source(
        center_id=center_id,
        school_year=school_year,
        ciclo=ciclo,
    )

    full_report = build_final_status_report(rows)

    report = _filter_final_status_report(
        report=full_report,
        situacion=situacion,
        curso=curso,
        grado=grado,
        seccion=seccion,
    )

    dashboard_payload = {
        "institution": {
            "name": _resolve_institution_name(),
            "school_year": _resolve_school_year(school_year),
            "ciclo": ciclo or "Vista general",
            "logos": _resolve_institution_logos(),
            "favicon": "/assets/interface_logo.png",
        },
        "filters": {
            "center_id": center_id,
            "school_year": school_year,
            "ciclo": ciclo,
            "situacion": situacion,
            "curso": curso,
            "grado": grado,
            "seccion": seccion,
        },
        "report": report,
    }

    rendered_html = _render_template_to_html(
        "final_status_report.html",
        request=request,
        dashboard_payload=dashboard_payload,
    )

    pdf_bytes = _render_pdf_bytes_from_html(
        rendered_html,
        base_url=str(request.base_url),
    )

    filename_parts = [
        "situacion_final",
        ciclo or "general",
        situacion or "resumen",
    ]

    filename = "_".join(
        str(part).replace(" ", "_").lower()
        for part in filename_parts
        if part
    )

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'inline; filename="{filename}.pdf"'
        },
    )


@router.get(
    "/proyeccion-completivo/data",
    name="academic_tracking_completivo_projection_data",
)
def completivo_projection_data(
    center_id: Optional[str] = Query(default=None),
    school_year: Optional[str] = Query(default=None),
    ciclo: Optional[str] = Query(default=None),
    curso: Optional[str] = Query(default=None),
    asignatura: Optional[str] = Query(default=None),
    riesgo: Optional[str] = Query(default=None),
    tendencia: Optional[str] = Query(default=None),
):
    rows = load_academic_rows_from_source(
        center_id=center_id,
        school_year=school_year,
        ciclo=ciclo,
    )

    report = build_completivo_projection_report(
        rows=rows,
        curso=curso,
        asignatura=asignatura,
        riesgo=riesgo,
        tendencia=tendencia,
    )

    return {
        "institution": {
            "name": _resolve_institution_name(),
            "school_year": _resolve_school_year(school_year),
            "ciclo": ciclo or "Vista general",
        },
        "filters": {
            "center_id": center_id,
            "school_year": school_year,
            "ciclo": ciclo,
            "curso": curso,
            "asignatura": asignatura,
            "riesgo": riesgo,
            "tendencia": tendencia,
        },
        "report": report,
    }


@router.get(
    "/proyeccion-completivo",
    response_class=HTMLResponse,
    name="academic_tracking_completivo_projection_dashboard",
)
def completivo_projection_dashboard(
    request: Request,
    center_id: Optional[str] = Query(default=None),
    school_year: Optional[str] = Query(default=None),
    ciclo: Optional[str] = Query(default=None),
    curso: Optional[str] = Query(default=None),
    asignatura: Optional[str] = Query(default=None),
    riesgo: Optional[str] = Query(default=None),
    tendencia: Optional[str] = Query(default=None),
):
    rows = load_academic_rows_from_source(
        center_id=center_id,
        school_year=school_year,
        ciclo=ciclo,
    )

    report = build_completivo_projection_report(
        rows=rows,
        curso=curso,
        asignatura=asignatura,
        riesgo=riesgo,
        tendencia=tendencia,
    )

    dashboard_payload = {
        "institution": {
            "name": _resolve_institution_name(),
            "school_year": _resolve_school_year(school_year),
            "ciclo": ciclo or "Vista general",
            "logos": _resolve_institution_logos(),
            "favicon": "/assets/interface_logo.png",
        },
        "theme": {
            "primary_color": "#1f8f4a",
            "primary_dark": "#0b3d24",
            "primary_soft": "#eaf5ef",
        },
        "filters": {
            "center_id": center_id,
            "school_year": school_year,
            "ciclo": ciclo,
            "curso": curso,
            "asignatura": asignatura,
            "riesgo": riesgo,
            "tendencia": tendencia,
        },
        "report": report,
    }

    return templates.TemplateResponse(
        "completivo_projection_dashboard.html",
        {
            "request": request,
            "dashboard": dashboard_payload,
        },
    )


@router.get(
    "/proyeccion-completivo/reporte.pdf",
    name="academic_tracking_completivo_projection_pdf",
)
def completivo_projection_pdf(
    request: Request,
    center_id: Optional[str] = Query(default=None),
    school_year: Optional[str] = Query(default=None),
    ciclo: Optional[str] = Query(default=None),
    curso: Optional[str] = Query(default=None),
    asignatura: Optional[str] = Query(default=None),
    riesgo: Optional[str] = Query(default=None),
    tendencia: Optional[str] = Query(default=None),
):
    rows = load_academic_rows_from_source(
        center_id=center_id,
        school_year=school_year,
        ciclo=ciclo,
    )

    report = build_completivo_projection_report(
        rows=rows,
        curso=curso,
        asignatura=asignatura,
        riesgo=riesgo,
        tendencia=tendencia,
    )

    dashboard_payload = {
        "institution": {
            "name": _resolve_institution_name(),
            "school_year": _resolve_school_year(school_year),
            "ciclo": ciclo or "Vista general",
            "logos": _resolve_institution_logos(),
            "favicon": "/assets/interface_logo.png",
        },
        "filters": {
            "center_id": center_id,
            "school_year": school_year,
            "ciclo": ciclo,
            "curso": curso,
            "asignatura": asignatura,
            "riesgo": riesgo,
            "tendencia": tendencia,
        },
        "report": report,
    }

    rendered_html = _render_template_to_html(
        "completivo_projection_report.html",
        request=request,
        dashboard_payload=dashboard_payload,
    )

    pdf_bytes = _render_pdf_bytes_from_html(
        rendered_html,
        base_url=str(request.base_url),
    )

    filename_parts = [
        "proyeccion_completivo",
        ciclo or "general",
        curso or "todos",
        asignatura or "todas",
        riesgo or "todos_los_riesgos",
        tendencia or "todas_las_tendencias",
    ]

    filename = "_".join(
        str(part).replace(" ", "_").lower()
        for part in filename_parts
        if part
    )

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'inline; filename="{filename}.pdf"'
        },
    )


@router.get(
    "/health",
    name="academic_tracking_health",
)
def healthcheck():
    return {
        "module": "academic_tracking",
        "status": "ok",
        "message": "Academic tracking module is running.",
    }