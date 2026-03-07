"""User entity and roles."""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from app.core.domain.value_objects import Email, UserId


@dataclass
class User:
    id: UserId
    email: str
    company_name: str
    stripe_customer_id: Optional[str]
    created_at: datetime

    @classmethod
    def from_store(cls, data: dict) -> "User":
        return cls(
            id=UserId(data["id"]),
            email=data["email"],
            company_name=data.get("company_name") or "",
            stripe_customer_id=data.get("stripe_customer_id"),
            created_at=datetime.fromisoformat(data["created_at"].replace("Z", "+00:00"))
            if isinstance(data.get("created_at"), str)
            else data.get("created_at", datetime.utcnow()),
        )

    def to_store(self, include_password_hash: bool = False, password_hash: Optional[str] = None) -> dict:
        out = {
            "id": str(self.id),
            "email": self.email,
            "company_name": self.company_name,
            "stripe_customer_id": self.stripe_customer_id,
            "created_at": self.created_at.isoformat(),
        }
        if include_password_hash and password_hash:
            out["password_hash"] = password_hash
        return out
