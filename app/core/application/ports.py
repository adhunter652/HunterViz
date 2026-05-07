"""Abstract interfaces (ports) for infrastructure."""
from abc import ABC, abstractmethod
from typing import Optional

from app.core.domain.value_objects import Email, UserId


class UserRepository(ABC):
    @abstractmethod
    def get_by_id(self, user_id: UserId) -> Optional[dict]:
        """Return user dict (id, email, company_name, stripe_customer_id, created_at) or None."""
        ...

    @abstractmethod
    def get_by_email(self, email: Email) -> Optional[dict]:
        """Return user dict including password_hash for verification, or None."""
        ...

    @abstractmethod
    def save(self, user: dict) -> None:
        """Create or update user. Must include id, email, password_hash, company_name, etc."""
        ...


class SubscriptionRepository(ABC):
    @abstractmethod
    def get_active_by_user_id(self, user_id: UserId) -> Optional[dict]:
        """Return active subscription for user or None."""
        ...

    @abstractmethod
    def save(self, subscription: dict) -> None:
        """Create or update subscription."""
        ...


class CompanyRepository(ABC):
    @abstractmethod
    def get_by_id(self, company_id: str) -> Optional[dict]:
        """Return company dict (id, name, owner_id, members) or None."""
        ...

    @abstractmethod
    def list_by_owner(self, owner_id: str) -> list[dict]:
        """Return list of companies owned by user."""
        ...

    @abstractmethod
    def list_by_member_email(self, email: str) -> list[dict]:
        """Return list of companies where user is a member."""
        ...

    @abstractmethod
    def save(self, company: dict) -> None:
        """Create or update company."""
        ...
