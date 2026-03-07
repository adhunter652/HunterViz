"""App entry: mount core + feature routers, static landing."""
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.core.api.middleware import setup_middleware
from app.core.config import get_settings
from app.features.auth.api.routes import router as auth_router
from app.features.subscriptions.api.routes import router as subscriptions_router
from app.features.business_display.api.routes import app_router

app = FastAPI(title="HunterViz", version="1.0.0")

setup_middleware(app)

settings = get_settings()
settings.ensure_data_dirs()

# API
app.include_router(auth_router, prefix="/api/v1")
app.include_router(subscriptions_router, prefix="/api/v1")

# App pages (sign-in, sign-up, user landing, subscribe)
app.include_router(app_router, prefix="/app")

# Static landing (main page). With Firebase Hosting, / is served by Hosting; Cloud Run only sees /app and /api.
static_dir = Path(__file__).resolve().parent.parent / "static"
if static_dir.exists():
    app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")


@app.get("/health")
def health():
    return {"status": "ok"}
