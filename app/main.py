"""App entry: mount core + feature routers, static landing."""
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.core.api.middleware import setup_middleware
from app.core.config import get_settings
from app.features.auth.api.routes import pages_router as auth_pages_router, router as auth_router
from app.features.subscriptions.api.routes import pages_router as subscriptions_pages_router, router as subscriptions_router

settings = get_settings()
app = FastAPI(title=settings.app_name, version="1.0.0")


def _validate_secret_key_for_production() -> None:
    """Fail startup if production and SECRET_KEY is missing or default placeholder."""
    from app.core.config import SECRET_KEY_DEFAULT_PLACEHOLDER
    if settings.is_production() and (
        not settings.secret_key or settings.secret_key == SECRET_KEY_DEFAULT_PLACEHOLDER
    ):
        raise RuntimeError(
            "SECRET_KEY must be set to a strong value in production; "
            "never use the default placeholder. Use Secret Manager or a secure env var."
        )


@app.on_event("startup")
def startup():
    _validate_secret_key_for_production()
    settings.ensure_data_dirs()


setup_middleware(app, allowed_origins=settings.get_cors_origins_list())

# API
app.include_router(auth_router, prefix="/api/v1")
app.include_router(subscriptions_router, prefix="/api/v1")

# App pages: each feature serves its own templates at /app
app.include_router(auth_pages_router, prefix="/app")
app.include_router(subscriptions_pages_router, prefix="/app")

# Static files and landing page
static_dir = Path(__file__).resolve().parent.parent / "static"
if static_dir.exists():
    # Mount /assets first so images are always served (e.g. /assets/logo.png)
    assets_dir = static_dir / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

    index_path = static_dir / "index.html"
    if index_path.exists():
        _landing_html = index_path.read_text(encoding="utf-8")

        @app.get("/", response_class=HTMLResponse)
        def landing_page():
            html = _landing_html.replace("{{APP_NAME}}", settings.app_name)
            return HTMLResponse(html)

    # Do not mount "/" with StaticFiles so the route above always serves the landing (with {{APP_NAME}} replaced).
    # Only /assets is mounted so images and other assets load.


@app.get("/health")
def health():
    return {"status": "ok"}


# Unsupported URLs: redirect to static site (must be last so it only matches when no route does)
STATIC_SITE_URL = "https://hunterviz.com"


@app.get("/{full_path:path}")
def redirect_unsupported_to_static_site(full_path: str):
    return RedirectResponse(url=STATIC_SITE_URL, status_code=302)
