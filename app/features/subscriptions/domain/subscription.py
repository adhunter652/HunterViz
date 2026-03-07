"""Subscription, Plan, status."""
from enum import Enum
from typing import Optional


class SubscriptionStatus(str, Enum):
    active = "active"
    past_due = "past_due"
    canceled = "canceled"
    trialing = "trialing"


# Plan shown on subscribe page
DEFAULT_PLAN = {
    "id": "pro",
    "name": "Pro",
    "description": "Full access to HunterViz dashboard and analytics.",
    "contact_sales": True,
}
