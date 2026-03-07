"""Check subscription status; used by business_display and subscribe page."""
from typing import Optional

from app.core.application.ports import SubscriptionRepository
from app.core.domain.value_objects import UserId
from app.features.subscriptions.domain.subscription import DEFAULT_PLAN


class SubscriptionService:
    def __init__(self, subscription_repository: SubscriptionRepository):
        self._repo = subscription_repository

    def get_active_subscription(self, user_id: UserId) -> Optional[dict]:
        return self._repo.get_active_by_user_id(user_id)

    def is_subscribed(self, user_id: UserId) -> bool:
        return self.get_active_subscription(user_id) is not None

    @staticmethod
    def get_plan_display() -> dict:
        return DEFAULT_PLAN
