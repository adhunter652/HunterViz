"""Auth view routes: sign-in, sign-up, user landing pages."""
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from app.core.api.deps import get_config
from app.core.config import Settings
from app.core.domain.value_objects import UserId
from app.features.auth.view.pages import signin_html, signup_html, user_landing_html

router = APIRouter(tags=["auth-views"])


@router.get("/login", response_class=HTMLResponse)
def login_page(config: Settings = Depends(get_config)):
    return HTMLResponse(signin_html(config.app_name))


@router.get("/signup", response_class=HTMLResponse)
def signup_page(config: Settings = Depends(get_config)):
    return HTMLResponse(signup_html(config.app_name))


@router.get("", response_class=HTMLResponse)
@router.get("/", response_class=HTMLResponse)
def user_landing(
    request: Request,
    config: Settings = Depends(get_config),
):
    """User landing: requires auth via token in request (e.g. from cookie or redirect with token)."""
    auth = request.headers.get("Authorization") or ""
    token = auth.replace("Bearer ", "").strip()
    if not token and request.cookies:
        token = request.cookies.get("access_token", "")
    if not token:
        return RedirectResponse(url="/app/login", status_code=302)
    from app.core.infrastructure.jwt_utils import decode_token

    payload = decode_token(token, config.secret_key)
    if not payload:
        return RedirectResponse(url="/app/login", status_code=302)
    user_id = payload.get("sub")
    if not user_id:
        return RedirectResponse(url="/app/login", status_code=302)
    from app.features.auth.infrastructure.user_store import JsonUserStore
    from app.features.subscriptions.infrastructure.subscription_store import (
        JsonSubscriptionStore,
    )

    user_store = JsonUserStore(config.user_store_path)
    sub_store = JsonSubscriptionStore(config.subscription_store_path)
    user = user_store.get_by_id(UserId(user_id))
    if not user:
        return RedirectResponse(url="/app/login", status_code=302)
    sub = sub_store.get_active_by_user_id(UserId(user_id))
    company_name = user.get("company_name") or "My Company"
    return HTMLResponse(
        user_landing_html(
            config.app_name, company_name, sub is not None, config.dashboard_url
        )
    )
