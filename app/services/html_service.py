# app/services/html_service.py

import base64
import mimetypes
import re
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.core.settings import settings
from app.utils.helpers import is_low_grade

TEMPLATES_DIR = Path("app/pdf/templates")
CSS_DIR = TEMPLATES_DIR / "css"


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


env = Environment(
    loader=FileSystemLoader(TEMPLATES_DIR),
    autoescape=select_autoescape(["html", "xml"])
)

env.globals["is_low_grade"] = is_low_grade
env.globals["helpers"] = SimpleNamespace(is_low_grade=is_low_grade)
env.globals["settings"] = settings


def _get_setting(name: str, default=""):
    return getattr(settings, name, default)


def build_image_data_uri(image_path: str) -> str:
    if not image_path:
        return ""

    try:
        file_path = Path(image_path)

        if not file_path.is_absolute():
            file_path = _project_root() / file_path

        if not file_path.exists():
            print(f"[HTML] No se encontró la imagen: {file_path}", flush=True)
            return ""

        mime_type, _ = mimetypes.guess_type(str(file_path))
        if not mime_type:
            mime_type = "image/png"

        encoded = base64.b64encode(file_path.read_bytes()).decode("utf-8")
        return f"data:{mime_type};base64,{encoded}"
    except Exception as exc:
        print(f"[HTML] No se pudo convertir la imagen a data URI ({image_path}): {exc}", flush=True)
        return ""


def load_css_text(css_filename: str) -> str:
    if not css_filename:
        return ""

    try:
        css_path = CSS_DIR / css_filename
        css_path = (_project_root() / css_path).resolve()

        if not css_path.exists():
            print(f"[HTML] No se encontró el CSS: {css_path}", flush=True)
            return ""

        return css_path.read_text(encoding="utf-8")
    except Exception as exc:
        print(f"[HTML] No se pudo leer el CSS ({css_filename}): {exc}", flush=True)
        return ""


def build_base_context(context: dict | None = None) -> dict:
    safe_context = dict(context or {})

    if "settings" not in safe_context:
        safe_context["settings"] = settings

    if "helpers" not in safe_context:
        safe_context["helpers"] = SimpleNamespace(is_low_grade=is_low_grade)

    if "generated_at" not in safe_context:
        safe_context["generated_at"] = datetime.now().strftime("%d/%m/%Y %I:%M %p")

    if "generated_by" not in safe_context:
        safe_context["generated_by"] = _get_setting("bulletin_generated_by", "Sistema de Boletines")

    if "generated_role" not in safe_context:
        safe_context["generated_role"] = _get_setting("bulletin_generated_role", "")

    if "director_name" not in safe_context:
        safe_context["director_name"] = _get_setting("institution_director", "")

    if "school_year" not in safe_context:
        safe_context["school_year"] = _get_setting("school_year", "2025-2026")

    if "institution_logo_src" not in safe_context:
        safe_context["institution_logo_src"] = build_image_data_uri(
            _get_setting("institution_logo", "")
        )

    if "minerd_logo_src" not in safe_context:
        safe_context["minerd_logo_src"] = build_image_data_uri(
            _get_setting("institution_minerd_logo", "")
        )

    if "letterhead_src" not in safe_context:
        safe_context["letterhead_src"] = build_image_data_uri(
            _get_setting("institution_letterhead", "")
        )

    # CSS WEB (se mantiene solo para vistas web)
    if "bulletin_base_css" not in safe_context:
        safe_context["bulletin_base_css"] = load_css_text("bulletin_base.css")

    if "bulletin_specific_css" not in safe_context:
        safe_context["bulletin_specific_css"] = ""

    # CSS PDF
    if "bulletin_cover_pdf_css" not in safe_context:
        safe_context["bulletin_cover_pdf_css"] = load_css_text("bulletin_cover_pdf.css")

    if "bulletin_pdf_css" not in safe_context:
        safe_context["bulletin_pdf_css"] = load_css_text("bulletin_pdf.css")

    return safe_context


def render_template(template_name: str, context: dict) -> str:
    template = env.get_template(template_name)
    safe_context = build_base_context(context)
    return template.render(**safe_context)


def render_second_cycle_modules_only(student: dict, extra_context: dict | None = None) -> str:
    context = {
        "student": student,
        **(extra_context or {})
    }
    return render_template("second_cycle_modules_only.html", context)


def render_second_cycle_blocks_and_modules(student: dict, extra_context: dict | None = None) -> str:
    context = {
        "student": student,
        **(extra_context or {})
    }
    return render_template("second_cycle_blocks_and_modules.html", context)


def render_second_cycle_full(student: dict, extra_context: dict | None = None) -> str:
    context = {
        "student": student,
        **(extra_context or {})
    }
    return render_template("second_cycle_bulletin.html", context)


def extract_page_inner_content(rendered_html: str) -> str:
    """
    Extrae el contenido útil de los HTML web para reutilizarlo dentro de los
    templates PDF, sin toolbar ni scripts.
    """
    if not rendered_html:
        return ""

    html = re.sub(
        r"<script\b[^>]*>.*?</script>",
        "",
        rendered_html,
        flags=re.IGNORECASE | re.DOTALL,
    )

    # elimina toolbar
    html = re.sub(
        r'<div class="screen-toolbar".*?</div>',
        "",
        html,
        flags=re.IGNORECASE | re.DOTALL,
    )

    match = re.search(
        r'<div class="page-inner">\s*(.*)\s*</div>\s*</div>\s*</div>\s*</div>',
        html,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if match:
        return match.group(1).strip()

    body_match = re.search(
        r"<body[^>]*>(.*)</body>",
        html,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if body_match:
        return body_match.group(1).strip()

    return rendered_html


def render_first_cycle_complete_pdf(student: dict, cycle: str, page2_content: str, extra_context: dict | None = None) -> str:
    context = {
        "student": student,
        "cycle": cycle,
        "page2_content": page2_content,
        **(extra_context or {})
    }
    return render_template("first_cycle_complete_pdf.html", context)


def render_first_cycle_blocks_pdf(student: dict, cycle: str, page2_content: str, extra_context: dict | None = None) -> str:
    context = {
        "student": student,
        "cycle": cycle,
        "page2_content": page2_content,
        **(extra_context or {})
    }
    return render_template("first_cycle_blocks_pdf.html", context)


def render_second_cycle_complete_pdf(student: dict, cycle: str, page2_content: str, extra_context: dict | None = None) -> str:
    context = {
        "student": student,
        "cycle": cycle,
        "page2_content": page2_content,
        **(extra_context or {})
    }
    return render_template("second_cycle_complete_pdf.html", context)


def render_second_cycle_modules_only_pdf(student: dict, cycle: str, page2_content: str, extra_context: dict | None = None) -> str:
    context = {
        "student": student,
        "cycle": cycle,
        "page2_content": page2_content,
        **(extra_context or {})
    }
    return render_template("second_cycle_modules_only_pdf.html", context)


def render_second_cycle_blocks_and_modules_pdf(student: dict, cycle: str, page2_content: str, extra_context: dict | None = None) -> str:
    context = {
        "student": student,
        "cycle": cycle,
        "page2_content": page2_content,
        **(extra_context or {})
    }
    return render_template("second_cycle_blocks_and_modules_pdf.html", context)