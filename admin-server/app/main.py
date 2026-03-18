"""Admin server entry. Separate from main app; IAP handles auth."""
import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from app.core.api.middleware import setup_middleware
from app.core.config import get_settings
from app.core.infrastructure.gcs_sync import start_background_sync, sync_from_bucket
from app.features.users.api.routes import router as users_router

logger = logging.getLogger(__name__)

settings = get_settings()
app = FastAPI(title=settings.app_name, version="1.0.0")


@app.on_event("startup")
def startup():
    settings.ensure_data_dirs()
    try:
        sync_from_bucket(settings)
        if settings.gcs_data_bucket:
            start_background_sync(get_settings)
    except Exception as e:
        logger.warning("GCS sync disabled at startup: %s", e, exc_info=True)


setup_middleware(app, allowed_origins=settings.get_cors_origins_list())

app.include_router(users_router)


@app.get("/")
def index():
    return RedirectResponse(url="/users", status_code=302)


@app.get("/health")
def health():
    return {"status": "ok"}
