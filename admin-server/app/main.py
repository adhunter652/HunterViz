"""Admin server entry. Separate from main app; IAP handles auth."""
import logging
import threading

from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from fastapi.staticfiles import StaticFiles
from app.core.api.middleware import setup_middleware
from app.core.config import get_settings
from app.core.infrastructure.gcs_sync import start_background_sync, sync_from_bucket
from app.features.users.api.routes import router as users_router

logger = logging.getLogger(__name__)

settings = get_settings()
app = FastAPI(title=settings.app_name, version="1.0.0")

# Mount static files for favicon and assets
app.mount("/assets", StaticFiles(directory="static/assets"), name="assets")


def _do_initial_sync() -> None:
    """Run in background so we don't block server from binding to PORT (Cloud Run startup timeout)."""
    try:
        s = get_settings()
        s.ensure_data_dirs()
        sync_from_bucket(s)
        if s.gcs_data_bucket:
            start_background_sync(get_settings)
    except Exception as e:
        logger.warning("GCS sync disabled at startup: %s", e, exc_info=True)


@app.on_event("startup")
def startup():
    # Defer GCS sync to a thread so the server can bind to PORT immediately and pass Cloud Run's health check.
    threading.Thread(target=_do_initial_sync, daemon=True, name="initial-gcs-sync").start()


setup_middleware(app, allowed_origins=settings.get_cors_origins_list())

app.include_router(users_router)


@app.get("/")
def index():
    return RedirectResponse(url="/users", status_code=302)


@app.get("/health")
def health():
    return {"status": "ok"}
