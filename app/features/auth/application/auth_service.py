"""Register, login, verify token."""
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from passlib.context import CryptContext

from app.core.domain.value_objects import Email, UserId
from app.core.application.ports import UserRepository

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(user_id: str, secret_key: str, expire_minutes: int = 15) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "exp": now + timedelta(minutes=expire_minutes),
        "iat": now,
        "type": "access",
    }
    return jwt.encode(payload, secret_key, algorithm="HS256")


def create_refresh_token(user_id: str, secret_key: str, expire_days: int = 7) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "exp": now + timedelta(days=expire_days),
        "iat": now,
        "type": "refresh",
    }
    return jwt.encode(payload, secret_key, algorithm="HS256")


class AuthService:
    def __init__(
        self,
        user_repository: UserRepository,
        secret_key: str,
        access_token_expire_minutes: int = 15,
        refresh_token_expire_days: int = 7,
    ):
        self._repo = user_repository
        self._secret_key = secret_key
        self._access_expire = access_token_expire_minutes
        self._refresh_expire = refresh_token_expire_days

    def register(
        self,
        email: str,
        password: str,
        company_name: str = "",
    ) -> dict:
        email_val = Email(email.strip().lower())
        existing = self._repo.get_by_email(email_val)
        if existing:
            raise ValueError("Email already registered")
        user_id = UserId(str(uuid.uuid4()))
        password_hash = hash_password(password)
        now = datetime.now(timezone.utc)
        user_data = {
            "id": str(user_id),
            "email": email_val,
            "password_hash": password_hash,
            "company_name": company_name.strip() or "My Company",
            "stripe_customer_id": None,
            "created_at": now.isoformat(),
        }
        self._repo.save(user_data)
        return {
            "id": str(user_id),
            "email": email_val,
            "company_name": user_data["company_name"],
        }

    def login(self, email: str, password: str) -> dict:
        email_val = Email(email.strip().lower())
        user_data = self._repo.get_by_email(email_val)
        if not user_data:
            raise ValueError("Invalid email or password")
        if not verify_password(password, user_data["password_hash"]):
            raise ValueError("Invalid email or password")
        user_id = user_data["id"]
        access = create_access_token(user_id, self._secret_key, self._access_expire)
        refresh = create_refresh_token(user_id, self._secret_key, self._refresh_expire)
        return {
            "access_token": access,
            "refresh_token": refresh,
            "token_type": "bearer",
            "user": {
                "id": user_id,
                "email": user_data["email"],
                "company_name": user_data.get("company_name") or "",
            },
        }

    def get_user_by_id(self, user_id: UserId) -> Optional[dict]:
        data = self._repo.get_by_id(user_id)
        if not data:
            return None
        return {
            "id": data["id"],
            "email": data["email"],
            "company_name": data.get("company_name") or "",
        }
