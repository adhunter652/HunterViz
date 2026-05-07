"""Checkout, portal, webhook; plan info and subscribe/contact pages from templates.

When adding a Stripe webhook endpoint (e.g. POST /api/v1/webhooks/stripe), you must verify
every request with stripe.Webhook.construct_event(payload, signature_header, webhook_secret)
using STRIPE_WEBHOOK_SECRET before processing. See docs/SECURITY.md."""
import json
import smtplib
from email.mime.text import MIMEText
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from app.core.api.deps import get_config, get_current_user_id
from app.core.config import Settings
from app.core.domain.value_objects import UserId
from app.core.infrastructure.gcs_sync import push_data_file
from app.core.infrastructure.templating import render_template
from app.features.subscriptions.application.subscription_service import SubscriptionService
from app.features.subscriptions.domain.subscription import DEFAULT_PLAN

router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])
pages_router = APIRouter(tags=["subscription-views"])


class ContactFormBody(BaseModel):
    full_name: str
    email: str
    company_size: Optional[str] = None
    analytics_needs: Optional[str] = None
    primary_data_source: Optional[str] = None
    phone: Optional[str] = None


def get_subscription_service(settings: Settings) -> SubscriptionService:
    from app.features.subscriptions.infrastructure.subscription_store import JsonSubscriptionStore
    repo = JsonSubscriptionStore(settings.subscription_store_path)
    return SubscriptionService(repo)


@router.get("/plan")
def get_plan():
    """Public: plan details for subscribe page."""
    return DEFAULT_PLAN


@router.get("/status")
def subscription_status(
    user_id: UserId = Depends(get_current_user_id),
    config: Settings = Depends(get_config),
):
    """Whether current user has an active subscription."""
    service = get_subscription_service(config)
    sub = service.get_active_subscription(user_id)
    return {"subscribed": sub is not None, "subscription": sub}


def _send_contact_email(
    config: Settings,
    body: ContactFormBody,
    *,
    user_email: Optional[str] = None,
    user_company_name: Optional[str] = None,
) -> None:
    """Email form body to contact_email if SMTP is configured; else append to file."""
    lines = [
        "Contact form submission",
        "",
        f"Name: {body.full_name}",
        f"Business name: {user_company_name or '(not provided)'}",
        f"Email: {user_email or '(not provided)'}",
        "",
        "Form answers:",
        f"Company Size: {body.company_size or '(not provided)'}",
        f"Analytics Needs: {body.analytics_needs or '(not provided)'}",
        f"Primary Data Source: {body.primary_data_source or '(not provided)'}",
        f"Phone: {body.phone or '(not provided)'}",
    ]
    text = "\n".join(lines)
    if config.smtp_host and config.smtp_user and config.smtp_password:
        from_addr = config.smtp_from or config.smtp_user
        msg = MIMEText(text, "plain", "utf-8")
        msg["Subject"] = "Contact form submission"
        msg["From"] = from_addr
        msg["To"] = config.contact_email
        with smtplib.SMTP(config.smtp_host, config.smtp_port) as smtp:
            smtp.starttls()
            smtp.login(config.smtp_user, config.smtp_password)
            smtp.sendmail(from_addr, [config.contact_email], msg.as_string())
    else:
        path = Path(config.subscription_store_path).parent / "contact_submissions.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        submissions = []
        if path.exists():
            try:
                submissions = json.loads(path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                submissions = []
        record = body.model_dump()
        record["user_email"] = user_email
        record["user_company_name"] = user_company_name
        record["full_name"] = body.full_name
        submissions.append(record)
        path.write_text(json.dumps(submissions, indent=2), encoding="utf-8")
        push_data_file(config, path)


def get_auth_service(settings: Settings):
    from app.features.auth.application.auth_service import AuthService
    from app.features.auth.infrastructure.firestore_user_store import FirestoreUserStore
    from app.features.auth.infrastructure.firestore_company_store import FirestoreCompanyStore
    user_repo = FirestoreUserStore()
    company_repo = FirestoreCompanyStore()
    return AuthService(
        user_repository=user_repo,
        secret_key=settings.secret_key,
        access_token_expire_minutes=settings.access_token_expire_minutes,
        refresh_token_expire_days=settings.refresh_token_expire_days,
        company_repository=company_repo,
    )


from app.core.api.deps import get_config, get_current_user_id, get_current_user_id_optional


@router.post("/contact")
def submit_contact_form(
    body: ContactFormBody,
    user_id: Optional[UserId] = Depends(get_current_user_id_optional),
    config: Settings = Depends(get_config),
):
    """Accept contact sales form and email to contact_email (or store if SMTP not set)."""
    user_email = body.email
    user_company_name = None

    if user_id:
        auth = get_auth_service(config)
        user = auth.get_user_by_id(user_id)
        if user:
            # If logged in, we can still use the body email but maybe capture company from profile
            user_company_name = user.get("company_name")

    # If body has a name, use it; else use what we found in profile if any
    full_name = body.full_name

    _send_contact_email(
        config, body,
        user_email=user_email,
        user_company_name=user_company_name,
    )
    return {"ok": True}


# --- App pages (HTML from feature templates) ---


@pages_router.get("/subscribe", response_class=HTMLResponse)
def subscribe_page(config: Settings = Depends(get_config)):
    p = DEFAULT_PLAN
    return HTMLResponse(
        render_template(
            "subscriptions",
            "subscribe",
            {
                "app_name": config.app_name,
                "plan_name": p["name"],
                "plan_description": p["description"],
                "contact_sales": p.get("contact_sales", True),
                "contact_phone": config.contact_phone,
                "contact_email": config.contact_email,
            },
        )
    )


@pages_router.get("/contact", response_class=HTMLResponse)
def contact_form_page(
    config: Settings = Depends(get_config),
    user_id: Optional[UserId] = Depends(get_current_user_id_optional),
):
    user_email = ""
    full_name = ""
    if user_id:
        auth = get_auth_service(config)
        user = auth.get_user_by_id(user_id)
        if user:
            user_email = user.get("email") or ""
            full_name = f"{user.get('first_name', '')} {user.get('last_name', '')}".strip()

    return HTMLResponse(
        render_template(
            "subscriptions",
            "contact",
            {
                "app_name": config.app_name,
                "user_email": user_email,
                "full_name": full_name,
            },
        )
    )
