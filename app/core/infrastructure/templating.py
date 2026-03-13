"""Render HTML from feature templates (no raw HTML in Python)."""
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

_BASE = Path(__file__).resolve().parent.parent.parent
_FEATURES = _BASE / "features"
_env_cache: dict[str, Environment] = {}


def _get_env(feature: str) -> Environment:
    if feature not in _env_cache:
        templates_dir = _FEATURES / feature / "templates"
        templates_dir.mkdir(parents=True, exist_ok=True)
        _env_cache[feature] = Environment(
            loader=FileSystemLoader(str(templates_dir)),
            autoescape=True,
        )
    return _env_cache[feature]


def render_template(feature: str, template_name: str, context: dict) -> str:
    """Load and render a feature's .html template. Template lives in features/<feature>/templates/."""
    env = _get_env(feature)
    name = template_name if template_name.endswith(".html") else f"{template_name}.html"
    return env.get_template(name).render(**context)
