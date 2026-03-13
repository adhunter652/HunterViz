"""App entry: mount core + feature routers, static landing."""
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from app.core.api.middleware import setup_middleware
from app.core.config import get_settings
from app.features.auth.api.routes import pages_router as auth_pages_router, router as auth_router
from app.features.subscriptions.api.routes import pages_router as subscriptions_pages_router, router as subscriptions_router

settings = get_settings()
app = FastAPI(title=settings.app_name, version="1.0.0")

setup_middleware(app)
settings.ensure_data_dirs()

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
