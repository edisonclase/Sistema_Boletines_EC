from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.utils.helpers import is_low_grade

TEMPLATES_DIR = Path("app/pdf/templates")

env = Environment(
    loader=FileSystemLoader(TEMPLATES_DIR),
    autoescape=select_autoescape(["html", "xml"])
)

env.globals["is_low_grade"] = is_low_grade


def render_template(template_name: str, context: dict) -> str:
    template = env.get_template(template_name)
    return template.render(**context)