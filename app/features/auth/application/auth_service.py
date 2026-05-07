"""Register, login, verify token."""
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from passlib.context import CryptContext

from app.core.domain.value_objects import Email, UserId
from app.core.application.ports import UserRepository, CompanyRepository

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

BCRYPT_MAX_PASSWORD_BYTES = 72
MIN_PASSWORD_LENGTH = 8


def _truncate_password_bytes(password: str) -> bytes:
    """Bcrypt limits input to 72 bytes; truncate to avoid ValueError from bcrypt 5.x."""
    encoded = password.encode("utf-8")
    return encoded[:BCRYPT_MAX_PASSWORD_BYTES]


def hash_password(password: str) -> str:
    return pwd_context.hash(_truncate_password_bytes(password))


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(_truncate_password_bytes(plain), hashed)


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
        company_repository: Optional[CompanyRepository] = None,
    ):
        self._repo = user_repository
        self._secret_key = secret_key
        self._access_expire = access_token_expire_minutes
        self._refresh_expire = refresh_token_expire_days
        self._company_repo = company_repository

    def register(
        self,
        email: str,
        password: str,
        company_name: str = "",
    ) -> dict:
        if not password or len(password) < MIN_PASSWORD_LENGTH:
            raise ValueError(f"Password must be at least {MIN_PASSWORD_LENGTH} characters")
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
        
        if self._company_repo:
            self._company_repo.save({
                "name": user_data["company_name"],
                "owner_id": str(user_id),
                "members": {},
                "member_emails": []
            })
        
        return {
            "id": str(user_id),
            "email": email_val,
            "company_name": user_data["company_name"],
        }

    def get_or_create_google_user(self, email: str) -> dict:
        email_val = Email(email.strip().lower())
        user_data = self._repo.get_by_email(email_val)
        is_new = False
        if not user_data:
            user_id = UserId(str(uuid.uuid4()))
            now = datetime.now(timezone.utc)
            user_data = {
                "id": str(user_id),
                "email": email_val,
                "password_hash": None,  # No password for Google users
                "company_name": "",  # To be filled later
                "stripe_customer_id": None,
                "created_at": now.isoformat(),
                "auth_provider": "google",
            }
            self._repo.save(user_data)
            is_new = True
            
            if self._company_repo:
                self._company_repo.save({
                    "name": "My Company",
                    "owner_id": str(user_id),
                    "members": {},
                    "member_emails": []
                })
        
        user_id = user_data["id"]
        access = create_access_token(user_id, self._secret_key, self._access_expire)
        refresh = create_refresh_token(user_id, self._secret_key, self._refresh_expire)
        
        return {
            "access_token": access,
            "refresh_token": refresh,
            "token_type": "bearer",
            "is_new": is_new or not user_data.get("company_name"),
            "user": {
                "id": user_id,
                "email": user_data["email"],
                "company_name": user_data.get("company_name") or "",
            },
        }

    def update_company_name(self, user_id: UserId, company_name: str) -> None:
        user_data = self._repo.get_by_id(user_id)
        if not user_data:
            raise ValueError("User not found")
        user_data["company_name"] = company_name.strip()
        self._repo.save(user_data)

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
