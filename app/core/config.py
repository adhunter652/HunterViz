"""Settings from environment."""
from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # App
    app_name: str = "HunterViz"
    debug: bool = False

    # Auth
    secret_key: str = "change-me-in-production"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7

    # User store (JSON file)
    user_store_path: str = "data/users.json"

    # Subscription store
    subscription_store_path: str = "data/subscriptions.json"

    # Cloud Run / external URLs (for redirects from static site)
    cloud_run_url: str = ""  # e.g. https://your-service-xxx.run.app

    # Stripe (optional for subscribe page)
    stripe_secret_key: Optional[str] = None
    stripe_webhook_secret: Optional[str] = None
    stripe_price_id: Optional[str] = None

    # Dashboard URL (provided later)
    dashboard_url: str = "https://dashboard.hunterviz.com"

    def ensure_data_dirs(self) -> None:
        Path(self.user_store_path).parent.mkdir(parents=True, exist_ok=True)
        Path(self.subscription_store_path).parent.mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    return Settings()
