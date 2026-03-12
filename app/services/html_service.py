# app/services/html_service.py

import base64
import mimetypes
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.core.settings import settings
from app.utils.helpers import is_low_grade

TEMPLATES_DIR = Path("app/pdf/templates")

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
            file_path = Path.cwd() / file_path

        if not file_path.exists():
            return ""

        mime_type, _ = mimetypes.guess_type(str(file_path))
        if not mime_type:
            mime_type = "image/png"

        encoded = base64.b64encode(file_path.read_bytes()).decode("utf-8")
        return f"data:{mime_type};base64,{encoded}"
    except Exception:
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
    return render_template("second_cycle_full.html", context)