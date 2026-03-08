"""Subscription view routes: subscribe page."""
from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse

from app.core.api.deps import get_config
from app.core.config import Settings
from app.features.subscriptions.domain.subscription import DEFAULT_PLAN
from app.features.subscriptions.view.pages import subscribe_page_html

router = APIRouter(tags=["subscription-views"])


@router.get("/subscribe", response_class=HTMLResponse)
def subscribe_page(config: Settings = Depends(get_config)):
    p = DEFAULT_PLAN
    return HTMLResponse(
        subscribe_page_html(
            config.app_name,
            p["name"],
            p["description"],
            p.get("contact_sales", True),
        )
    )
