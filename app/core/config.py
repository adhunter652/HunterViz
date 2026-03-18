"""Settings from environment."""
from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


# Default placeholder; must be overridden in production (env or Secret Manager).
SECRET_KEY_DEFAULT_PLACEHOLDER = "change-me-in-production"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # App
    app_name: str = "HunterViz"
    debug: bool = False
    port: int = 8000  # Server port (use 8080 or another if 8000 gives WinError 10013 on Windows)

    # Auth
    secret_key: str = SECRET_KEY_DEFAULT_PLACEHOLDER
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7

    # User store (JSON file)
    user_store_path: str = "data/users.json"

    # Subscription store
    subscription_store_path: str = "data/subscriptions.json"

    # GCS data bucket: when set, JSON data files are synced to this bucket (pull on startup + every 20s, push on write).
    gcs_data_bucket: Optional[str] = None

    # App server URL (static site hunterviz.com links here for Sign in / Sign up / Contact)
    cloud_run_url: str = "https://app.hunterviz.com"

    # CORS: comma-separated origins when allow_credentials=True (e.g. https://app.hunterviz.com,https://hunterviz.com).
    # For local dev include your app origin (port must match PORT). Never use * with credentials.
    cors_origins: str = "http://localhost:8000,http://127.0.0.1:8000,http://localhost:8080,http://127.0.0.1:8080"

    # Cookie Secure flag: set True in production (HTTPS). Derived from cloud_run_url if not set.
    cookie_secure: Optional[bool] = None

    # Stripe (optional for subscribe page)
    stripe_secret_key: Optional[str] = None
    stripe_webhook_secret: Optional[str] = None
    stripe_price_id: Optional[str] = None

    # Dashboard URL (provided later)
    dashboard_url: str = "https://dashboard.example.com"

    # Contact (single source for subscribe / contact buttons)
    contact_phone: str = "4357207571"
    contact_email: str = "ammon@hunterviz.com"

    # Optional SMTP (to email contact form submissions to contact_email)
    smtp_host: Optional[str] = None
    smtp_port: int = 587
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_from: Optional[str] = None  # From address; defaults to smtp_user

    def ensure_data_dirs(self) -> None:
        Path(self.user_store_path).parent.mkdir(parents=True, exist_ok=True)
        Path(self.subscription_store_path).parent.mkdir(parents=True, exist_ok=True)

    def is_production(self) -> bool:
        """True when running in production (HTTPS app URL, not debug)."""
        return not self.debug and self.cloud_run_url.strip().lower().startswith("https://")

    def get_cookie_secure(self) -> bool:
        """Secure cookie flag: True in production (HTTPS), False in local dev."""
        if self.cookie_secure is not None:
            return self.cookie_secure
        return self.is_production()

    def get_cors_origins_list(self) -> list[str]:
        """CORS allowed origins; never empty when allow_credentials=True."""
        raw = (self.cors_origins or "").strip()
        if not raw:
            return ["http://localhost:8000", "http://127.0.0.1:8000", "http://localhost:8080", "http://127.0.0.1:8080"]
        return [o.strip() for o in raw.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
