"""Render HTML from templates. Jinja2 with autoescape=True (same as main app)."""
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

_BASE = Path(__file__).resolve().parent.parent.parent
_TEMPLATES = _BASE / "features" / "users" / "templates"
_env: Environment | None = None


def _get_env() -> Environment:
    global _env
    if _env is None:
        _TEMPLATES.mkdir(parents=True, exist_ok=True)
        _env = Environment(
            loader=FileSystemLoader(str(_TEMPLATES)),
            autoescape=True,
        )
    return _env


def render_template(template_name: str, context: dict) -> str:
    name = template_name if template_name.endswith(".html") else f"{template_name}.html"
    return _get_env().get_template(name).render(**context)
