from datetime import datetime

from fastapi import APIRouter, Depends, Query
from fastapi.responses import HTMLResponse, Response

from app.core.settings import settings
from app.security.auth_dependencies import (
    require_admin_or_registro,
    require_all_operational_roles,
    require_read_only_roles,
)
from app.services.audit_service import (
    log_course_zip_event,
    log_student_bulletin_event,
)
from app.services.bulletin_service import (
    find_student_by_id,
    get_available_courses,
    get_available_students,
)
from app.services.html_service import (
    render_template,
    render_second_cycle_blocks_and_modules,
    render_second_cycle_modules_only,
)
from app.services.pdf_service import (
    generate_blocks_and_modules_bulletin_pdf,
    generate_blocks_bulletin_pdf,
    generate_complete_bulletin_pdf,
    generate_course_blocks_and_modules_bulletins_zip,
    generate_course_blocks_bulletins_zip,
    generate_course_complete_bulletins_zip,
    generate_course_modules_only_bulletins_zip,
    generate_modules_only_bulletin_pdf,
)

router = APIRouter(prefix="/students", tags=["students"])


def _generated_by() -> str:
    return settings.bulletin_generated_by


def _generated_role() -> str:
    return settings.bulletin_generated_role


@router.get("/options/courses", dependencies=[Depends(require_all_operational_roles())])
def get_courses_options(cycle: str = Query(...)):
    return {
        "cycle": cycle,
        "courses": get_available_courses(cycle),
    }


@router.get("/options/students", dependencies=[Depends(require_all_operational_roles())])
def get_students_options(
    cycle: str = Query(...),
    course: str = Query(...),
):
    return {
        "cycle": cycle,
        "course": course,
        "students": get_available_students(cycle, course),
    }


@router.get("/{student_id}", dependencies=[Depends(require_read_only_roles())])
def get_student(student_id: str):
    return find_student_by_id(student_id)


@router.get(
    "/{student_id}/bulletin-html",
    response_class=HTMLResponse,
    dependencies=[Depends(require_admin_or_registro())],
)
def get_student_bulletin_html(student_id: str):
    result = find_student_by_id(student_id)

    if not result.get("found"):
        return HTMLResponse(
            content=f"<h1>No se encontró ningún estudiante con el ID {student_id}</h1>",
            status_code=404,
        )

    template_name = (
        "first_cycle_bulletin.html"
        if result["cycle"] == "Primer_Ciclo"
        else "second_cycle_bulletin.html"
    )

    html = render_template(
        template_name,
        {
            "institution_name": settings.institution_name,
            "student": result["student"],
            "cycle": result["cycle"],
            "logo_path": settings.institution_logo,
            "generated_at": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "generated_by": _generated_by(),
            "school_year": settings.school_year,
        },
    )

    log_student_bulletin_event(
        result=result,
        output_format="html",
        bulletin_type="complete",
        filename=f"{result['student'].get('id_estudiante', 'sin_id')} - vista_html_completa.html",
        generated_by=_generated_by(),
        generated_role=_generated_role(),
    )

    return HTMLResponse(content=html)


@router.get(
    "/{student_id}/bulletin-blocks-html",
    response_class=HTMLResponse,
    dependencies=[Depends(require_admin_or_registro())],
)
def get_student_bulletin_blocks_html(student_id: str):
    result = find_student_by_id(student_id)

    if not result.get("found"):
        return HTMLResponse(
            content=f"<h1>No se encontró ningún estudiante con el ID {student_id}</h1>",
            status_code=404,
        )

    if result["cycle"] != "Primer_Ciclo":
        return HTMLResponse(
            content="<h1>El boletín por bloques actualmente solo está disponible para Primer Ciclo.</h1>",
            status_code=400,
        )

    html = render_template(
        "first_cycle_blocks.html",
        {
            "institution_name": settings.institution_name,
            "student": result["student"],
            "cycle": result["cycle"],
            "logo_path": settings.institution_logo,
            "generated_at": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "generated_by": _generated_by(),
            "generated_role": _generated_role(),
            "director_name": settings.institution_director,
            "school_year": settings.school_year,
        },
    )

    log_student_bulletin_event(
        result=result,
        output_format="html",
        bulletin_type="blocks",
        filename=f"{result['student'].get('id_estudiante', 'sin_id')} - vista_html_bloques.html",
        generated_by=_generated_by(),
        generated_role=_generated_role(),
    )

    return HTMLResponse(content=html)


@router.get(
    "/{student_id}/second-cycle-blocks-html",
    response_class=HTMLResponse,
    dependencies=[Depends(require_admin_or_registro())],
)
def get_student_second_cycle_blocks_html(student_id: str):
    result = find_student_by_id(student_id)

    if not result.get("found"):
        return HTMLResponse(
            content=f"<h1>No se encontró ningún estudiante con el ID {student_id}</h1>",
            status_code=404,
        )

    if result["cycle"] != "Segundo_Ciclo":
        return HTMLResponse(
            content="<h1>El boletín por bloques y módulos solo está disponible para Segundo Ciclo.</h1>",
            status_code=400,
        )

    html = render_second_cycle_blocks_and_modules(result["student"])

    log_student_bulletin_event(
        result=result,
        output_format="html",
        bulletin_type="blocks_and_modules",
        filename=f"{result['student'].get('id_estudiante', 'sin_id')} - vista_html_bloques_modulos.html",
        generated_by=_generated_by(),
        generated_role=_generated_role(),
    )

    return HTMLResponse(content=html)


@router.get(
    "/{student_id}/modules-only-html",
    response_class=HTMLResponse,
    dependencies=[Depends(require_admin_or_registro())],
)
def get_student_modules_only_html(student_id: str):
    result = find_student_by_id(student_id)

    if not result.get("found"):
        return HTMLResponse(
            content=f"<h1>No se encontró ningún estudiante con el ID {student_id}</h1>",
            status_code=404,
        )

    if result["cycle"] != "Segundo_Ciclo":
        return HTMLResponse(
            content="<h1>El boletín de módulos solo está disponible para Segundo Ciclo.</h1>",
            status_code=400,
        )

    html = render_second_cycle_modules_only(result["student"])

    log_student_bulletin_event(
        result=result,
        output_format="html",
        bulletin_type="modules_only",
        filename=f"{result['student'].get('id_estudiante', 'sin_id')} - vista_html_modulos.html",
        generated_by=_generated_by(),
        generated_role=_generated_role(),
    )

    return HTMLResponse(content=html)


@router.get(
    "/{student_id}/modules-only-pdf",
    dependencies=[Depends(require_admin_or_registro())],
)
def get_student_modules_only_pdf(student_id: str):
    result = find_student_by_id(student_id)

    if not result.get("found"):
        return HTMLResponse(
            content=f"<h1>No se encontró ningún estudiante con el ID {student_id}</h1>",
            status_code=404,
        )

    if result["cycle"] != "Segundo_Ciclo":
        return HTMLResponse(
            content="<h1>El boletín de módulos solo está disponible para Segundo Ciclo.</h1>",
            status_code=400,
        )

    pdf_bytes, filename = generate_modules_only_bulletin_pdf(student_id)

    log_student_bulletin_event(
        result=result,
        output_format="pdf",
        bulletin_type="modules_only",
        filename=filename,
        generated_by=_generated_by(),
        generated_role=_generated_role(),
    )

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get(
    "/{student_id}/second-cycle-blocks-pdf",
    dependencies=[Depends(require_admin_or_registro())],
)
def get_student_second_cycle_blocks_pdf(student_id: str):
    result = find_student_by_id(student_id)

    if not result.get("found"):
        return HTMLResponse(
            content=f"<h1>No se encontró ningún estudiante con el ID {student_id}</h1>",
            status_code=404,
        )

    if result["cycle"] != "Segundo_Ciclo":
        return HTMLResponse(
            content="<h1>El boletín por bloques y módulos solo está disponible para Segundo Ciclo.</h1>",
            status_code=400,
        )

    pdf_bytes, filename = generate_blocks_and_modules_bulletin_pdf(student_id)

    log_student_bulletin_event(
        result=result,
        output_format="pdf",
        bulletin_type="blocks_and_modules",
        filename=filename,
        generated_by=_generated_by(),
        generated_role=_generated_role(),
    )

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get(
    "/{student_id}/bulletin-pdf",
    dependencies=[Depends(require_admin_or_registro())],
)
def get_student_bulletin_pdf(student_id: str):
    result = find_student_by_id(student_id)

    if not result.get("found"):
        return HTMLResponse(
            content=f"<h1>No se encontró ningún estudiante con el ID {student_id}</h1>",
            status_code=404,
        )

    pdf_bytes, filename = generate_complete_bulletin_pdf(student_id)

    log_student_bulletin_event(
        result=result,
        output_format="pdf",
        bulletin_type="complete",
        filename=filename,
        generated_by=_generated_by(),
        generated_role=_generated_role(),
    )

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get(
    "/{student_id}/bulletin-blocks-pdf",
    dependencies=[Depends(require_admin_or_registro())],
)
def get_student_bulletin_blocks_pdf(student_id: str):
    result = find_student_by_id(student_id)

    if not result.get("found"):
        return HTMLResponse(
            content=f"<h1>No se encontró ningún estudiante con el ID {student_id}</h1>",
            status_code=404,
        )

    if result["cycle"] != "Primer_Ciclo":
        return HTMLResponse(
            content="<h1>El boletín por bloques actualmente solo está disponible para Primer Ciclo.</h1>",
            status_code=400,
        )

    pdf_bytes, filename = generate_blocks_bulletin_pdf(student_id)

    log_student_bulletin_event(
        result=result,
        output_format="pdf",
        bulletin_type="blocks",
        filename=filename,
        generated_by=_generated_by(),
        generated_role=_generated_role(),
    )

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get(
    "/course/{cycle}/{course}/bulletins-zip",
    dependencies=[Depends(require_admin_or_registro())],
)
def get_course_complete_bulletins_zip(cycle: str, course: str):
    try:
        zip_bytes, filename = generate_course_complete_bulletins_zip(course=course, cycle=cycle)
        student_count = len(get_available_students(cycle, course))
    except ValueError as e:
        return HTMLResponse(content=f"<h1>{str(e)}</h1>", status_code=400)
    except FileNotFoundError as e:
        return HTMLResponse(content=f"<h1>{str(e)}</h1>", status_code=500)

    log_course_zip_event(
        cycle=cycle,
        course=course,
        bulletin_type="complete",
        filename=filename,
        student_count=student_count,
        generated_by=_generated_by(),
        generated_role=_generated_role(),
    )

    return Response(
        content=zip_bytes,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get(
    "/course/Primer_Ciclo/{course}/bulletins-blocks-zip",
    dependencies=[Depends(require_admin_or_registro())],
)
def get_course_blocks_bulletins_zip(course: str):
    try:
        zip_bytes, filename = generate_course_blocks_bulletins_zip(course=course)
        student_count = len(get_available_students("Primer_Ciclo", course))
    except ValueError as e:
        return HTMLResponse(content=f"<h1>{str(e)}</h1>", status_code=400)
    except FileNotFoundError as e:
        return HTMLResponse(content=f"<h1>{str(e)}</h1>", status_code=500)

    log_course_zip_event(
        cycle="Primer_Ciclo",
        course=course,
        bulletin_type="blocks",
        filename=filename,
        student_count=student_count,
        generated_by=_generated_by(),
        generated_role=_generated_role(),
    )

    return Response(
        content=zip_bytes,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get(
    "/course/Segundo_Ciclo/{course}/bulletins-modules-zip",
    dependencies=[Depends(require_admin_or_registro())],
)
def get_course_modules_only_bulletins_zip(course: str):
    try:
        zip_bytes, filename = generate_course_modules_only_bulletins_zip(course=course)
        student_count = len(get_available_students("Segundo_Ciclo", course))
    except ValueError as e:
        return HTMLResponse(content=f"<h1>{str(e)}</h1>", status_code=400)
    except FileNotFoundError as e:
        return HTMLResponse(content=f"<h1>{str(e)}</h1>", status_code=500)

    log_course_zip_event(
        cycle="Segundo_Ciclo",
        course=course,
        bulletin_type="modules_only",
        filename=filename,
        student_count=student_count,
        generated_by=_generated_by(),
        generated_role=_generated_role(),
    )

    return Response(
        content=zip_bytes,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get(
    "/course/Segundo_Ciclo/{course}/bulletins-blocks-and-modules-zip",
    dependencies=[Depends(require_admin_or_registro())],
)
def get_course_blocks_and_modules_bulletins_zip(course: str):
    try:
        zip_bytes, filename = generate_course_blocks_and_modules_bulletins_zip(course=course)
        student_count = len(get_available_students("Segundo_Ciclo", course))
    except ValueError as e:
        return HTMLResponse(content=f"<h1>{str(e)}</h1>", status_code=400)
    except FileNotFoundError as e:
        return HTMLResponse(content=f"<h1>{str(e)}</h1>", status_code=500)

    log_course_zip_event(
        cycle="Segundo_Ciclo",
        course=course,
        bulletin_type="blocks_and_modules",
        filename=filename,
        student_count=student_count,
        generated_by=_generated_by(),
        generated_role=_generated_role(),
    )

    return Response(
        content=zip_bytes,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
