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


def render_template(template_name: str, context: dict) -> str:
    template = env.get_template(template_name)

    safe_context = dict(context or {})

    if "settings" not in safe_context:
        safe_context["settings"] = settings

    if "helpers" not in safe_context:
        safe_context["helpers"] = SimpleNamespace(is_low_grade=is_low_grade)

    if "generated_at" not in safe_context:
        safe_context["generated_at"] = datetime.now().strftime("%d/%m/%Y %I:%M %p")

    if "generated_by" not in safe_context:
        safe_context["generated_by"] = settings.bulletin_generated_by

    if "generated_role" not in safe_context:
        safe_context["generated_role"] = settings.bulletin_generated_role

    if "director_name" not in safe_context:
        safe_context["director_name"] = settings.institution_director

    if "school_year" not in safe_context:
        safe_context["school_year"] = "2025-2026"

    return template.render(**safe_context)