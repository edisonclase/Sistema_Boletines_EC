"""
routes.py

Rutas del módulo academic_tracking.
"""

from __future__ import annotations

import re

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

        filename = path.replace("\\", "/").split("/")[-1]
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
    "/situacion-final/fichas.pdf",
    name="academic_tracking_final_status_slips_pdf",
)
def final_status_slips_pdf(
    request: Request,
    center_id: Optional[str] = Query(default=None),
    school_year: Optional[str] = Query(default=None),
    ciclo: Optional[str] = Query(default=None),
    situacion: Optional[str] = Query(default=None),
    curso: Optional[str] = Query(default=None),
    grado: Optional[str] = Query(default=None),
    seccion: Optional[str] = Query(default=None),
):
    def format_score(value: Any) -> str:
        if value is None:
            return "—"

        text = str(value).strip()

        if not text:
            return "—"

        try:
            number = float(text)
            return str(int(round(number)))
        except ValueError:
            return text

    def format_numero(value: Any) -> str:
        if value is None:
            return "—"

        text = str(value).strip()

        if not text:
            return "—"

        try:
            number = float(text)
            return str(int(number))
        except ValueError:
            return text

    rows = load_academic_rows_from_source(
        center_id=center_id,
        school_year=school_year,
        ciclo=ciclo,
    )

    full_report = build_final_status_report(rows)

    report = _filter_final_status_report(
        report=full_report,
        situacion=None,
        curso=curso,
        grado=grado,
        seccion=seccion,
    )

    normalized_situacion = _normalize_text(situacion)

    slip_students = []

    for student in report.get("students", []):
        slip_items = []

        if not normalized_situacion or normalized_situacion == "completivo":
            for subject in student.get("subjects_to_completivo", []):
                slip_items.append({
                    "name": subject.get("subject_name"),
                    "score": format_score(subject.get("cf_final")),
                    "stage": "completivo",
                    "item_type": "subject",
                })

        if not normalized_situacion or normalized_situacion == "extraordinario":
            for subject in student.get("subjects_to_extraordinario", []):
                slip_items.append({
                    "name": subject.get("subject_name"),
                    "score": format_score(subject.get("ccf")),
                    "stage": "extraordinario",
                    "item_type": "subject",
                })

        if not normalized_situacion or normalized_situacion == "especial":
            for subject in student.get("subjects_to_especial", []):
                slip_items.append({
                    "name": subject.get("subject_name"),
                    "score": format_score(subject.get("cexf")),
                    "stage": "especial",
                    "item_type": "subject",
                })

        if not normalized_situacion or normalized_situacion == "modulo_especial":
            for module in student.get("modules_to_special_evaluation", []):
                slip_items.append({
                    "name": module.get("module_name"),
                    "score": format_score(module.get("module_cf")),
                    "stage": "especial",
                    "item_type": "module",
                })

        if slip_items:
            student_copy = dict(student)
            student_copy["numero"] = format_numero(student.get("numero"))
            student_copy["slip_items"] = slip_items
            slip_students.append(student_copy)

    slip_students = sorted(
        slip_students,
        key=lambda item: (
            _normalize_text(item.get("course_name")),
            _normalize_text(item.get("numero")).zfill(4),
            _normalize_text(item.get("student_name")),
        ),
    )

    students_by_course = []
    course_map: dict[str, list[dict[str, Any]]] = {}

    for student in slip_students:
        course_name = _normalize_text(student.get("course_name")) or "Sin curso"
        course_map.setdefault(course_name, [])
        course_map[course_name].append(student)

    for course_name, students in course_map.items():
        students_by_course.append({
            "course_name": course_name,
            "prof_titular": students[0].get("prof_titular"),
            "students": students,
            })

    dashboard_payload = {
        "institution": {
            "name": _resolve_institution_name(),
            "school_year": _resolve_school_year(school_year),
            "ciclo": ciclo or "Vista general",
            "logos": [
                {
                    "src": "file:///D:/Sistema_Boletines_EC/academic_tracking/static/academic_tracking/images/logo.png",
                    "alt": "Logo del centro educativo",
                }
            ],
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
        "students": slip_students,
        "students_by_course": students_by_course,
    }

    rendered_html = _render_template_to_html(
        "final_status_student_slips.html",
        request=request,
        dashboard_payload=dashboard_payload,
    )

    pdf_bytes = _render_pdf_bytes_from_html(
        rendered_html,
        base_url=str(request.base_url),
    )

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": 'inline; filename="fichas_situacion_final.pdf"'
        },
    )
    
@router.get(
    "/situacion-final/constancia-entrega.pdf",
    name="academic_tracking_final_status_delivery_pdf",
)
def final_status_delivery_pdf(
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
        situacion=None,
        curso=curso,
        grado=grado,
        seccion=seccion,
    )

    normalized_situacion = _normalize_text(situacion)

    delivery_students = []

    for student in report.get("students", []):
        has_items = False

        if normalized_situacion == "completivo":
            has_items = bool(student.get("subjects_to_completivo"))

        elif normalized_situacion == "extraordinario":
            has_items = bool(student.get("subjects_to_extraordinario"))

        elif normalized_situacion == "especial":
            has_items = bool(student.get("subjects_to_especial"))

        elif normalized_situacion == "modulo_especial":
            has_items = bool(student.get("modules_to_special_evaluation"))

        else:
            has_items = bool(
                student.get("subjects_to_completivo")
                or student.get("subjects_to_extraordinario")
                or student.get("subjects_to_especial")
                or student.get("modules_to_special_evaluation")
            )

        if has_items:
            delivery_students.append(student)

    delivery_students = sorted(
        delivery_students,
        key=lambda item: (
            _normalize_text(item.get("course_name")),
            _normalize_text(item.get("numero")).zfill(4),
            _normalize_text(item.get("student_name")),
        ),
    )

    course_map: dict[str, list[dict[str, Any]]] = {}

    for student in delivery_students:
        course_name = _normalize_text(student.get("course_name")) or "Sin curso"
        course_map.setdefault(course_name, [])
        course_map[course_name].append(student)

    students_by_course = []

    for course_name, students in course_map.items():
        students_by_course.append({
            "course_name": course_name,
            "prof_titular": students[0].get("prof_titular"),
            "students": students,
        })

    dashboard_payload = {
        "institution": {
            "name": _resolve_institution_name(),
            "school_year": _resolve_school_year(school_year),
            "ciclo": ciclo or "Vista general",
            "logos": [
                {
                    "src": "file:///D:/Sistema_Boletines_EC/academic_tracking/static/academic_tracking/images/logo.png",
                    "alt": "Logo del centro educativo",
                }
            ],
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
        "students_by_course": students_by_course,
    }

    rendered_html = _render_template_to_html(
        "final_status_delivery_report.html",
        request=request,
        dashboard_payload=dashboard_payload,
    )

    pdf_bytes = _render_pdf_bytes_from_html(
        rendered_html,
        base_url=str(request.base_url),
    )

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": 'inline; filename="constancia_entrega_situacion_final.pdf"'
        },
    )
    
@router.get(
    "/recuperacion-pedagogica/fichas.pdf",
    name="academic_tracking_recovery_slips_pdf",
)
def recovery_slips_pdf(
    request: Request,
    center_id: Optional[str] = Query(default=None),
    school_year: Optional[str] = Query(default=None),
    ciclo: Optional[str] = Query(default=None),
    curso: Optional[str] = Query(default=None),
    grado: Optional[str] = Query(default=None),
    seccion: Optional[str] = Query(default=None),
    periodo: Optional[str] = Query(default=None),
    asignatura: Optional[str] = Query(default=None),
    min_approval_score: Optional[str] = Query(default=None),
):
    def format_score(value: Any) -> str:
        if value is None:
            return "—"

        try:
            return str(int(round(float(value))))
        except (TypeError, ValueError):
            return str(value).strip() or "—"

    def block_sort_key(label: str) -> tuple[int, str]:
        text = _normalize_text(label).upper()

        if "COMUNICATIVA" in text:
            return (1, text)

        if "PENSAMIENTO" in text or "LOGICO" in text or "LÓGICO" in text or "CREATIVO" in text or "CRITICO" in text or "CRÍTICO" in text or "RESOLUCION" in text or "RESOLUCIÓN" in text:
            return (2, text)

        if "CIENTIFICA" in text or "CIENTÍFICA" in text or "TECNOLOGICA" in text or "TECNOLÓGICA" in text or "AMBIENTAL" in text or "SALUD" in text:
            return (3, text)

        if "ETICA" in text or "ÉTICA" in text or "CIUDADANA" in text or "DESARROLLO" in text or "ESPIRITUAL" in text:
            return (4, text)

        return (99, text)

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
        student_status="en_riesgo",
        min_approval_score=min_score,
    )

    recovery_students = dashboard_payload.get("grouped_operational_rows", [])

    block_labels_map: dict[str, str] = {}

    for student in recovery_students:
        for subject in student.get("subjects", []):
            for block in subject.get("failed_blocks", []):
                block_label = str(block.get("block_label") or "").strip()

                if block_label:
                    block_key = block_label.upper()
                    block_labels_map[block_key] = block_label

    block_columns = [
        {
            "key": key,
            "label": label,
        }
        for key, label in sorted(
            block_labels_map.items(),
            key=lambda item: block_sort_key(item[1]),
        )
    ]

    for student in recovery_students:
        formatted_subjects = []

        for subject in student.get("subjects", []):
            block_scores = {
                column["key"]: "—"
                for column in block_columns
            }

            for block in subject.get("failed_blocks", []):
                block_label = str(block.get("block_label") or "").strip()

                if not block_label:
                    continue

                block_key = block_label.upper()
                block_scores[block_key] = format_score(block.get("score"))

            formatted_subjects.append(
                {
                    "subject_name": subject.get("subject_name"),
                    "blocks": block_scores,
                }
            )

        student["formatted_subjects"] = formatted_subjects

    dashboard_payload["students"] = recovery_students
    dashboard_payload["block_columns"] = block_columns
    dashboard_payload["filters"] = {
        **dashboard_payload.get("filters", {}),
        "center_id": center_id,
        "school_year": school_year,
        "ciclo": ciclo,
        "curso": curso,
        "grado": grado,
        "seccion": seccion,
        "periodo": periodo,
        "asignatura": asignatura,
    }

    rendered_html = _render_template_to_html(
        "period_recovery_student_slips.html",
        request=request,
        dashboard_payload=dashboard_payload,
    )

    pdf_bytes = _render_pdf_bytes_from_html(
        rendered_html,
        base_url=str(request.base_url),
    )

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": 'inline; filename="fichas_recuperacion_pedagogica.pdf"'
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