"""Checkout, portal, webhook; plan info for subscribe page."""
from fastapi import APIRouter, Depends

from app.core.api.deps import get_config, get_current_user_id
from app.core.config import Settings
from app.core.domain.value_objects import UserId
from app.features.subscriptions.application.subscription_service import SubscriptionService
from app.features.subscriptions.domain.subscription import DEFAULT_PLAN

router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])


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
