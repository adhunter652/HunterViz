"""Settings from environment. Same policies as main app: no secrets in code."""
from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class AdminSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # App
    app_name: str = "HunterViz Admin"
    debug: bool = False
    port: int = 8001

    # Same paths as main app so we read/write the same GCS blobs (users.json, etc.)
    user_store_path: str = "data/users.json"
    subscription_store_path: str = "data/subscriptions.json"

    # Same GCS bucket as main app
    gcs_data_bucket: Optional[str] = None

    # CORS: restrict to your admin origin (e.g. IAP URL). Never use * with credentials.
    cors_origins: str = "http://localhost:8001,http://127.0.0.1:8001"

    def ensure_data_dirs(self) -> None:
        Path(self.user_store_path).parent.mkdir(parents=True, exist_ok=True)
        Path(self.subscription_store_path).parent.mkdir(parents=True, exist_ok=True)

    def is_production(self) -> bool:
        return not self.debug

    def get_cors_origins_list(self) -> list[str]:
        raw = (self.cors_origins or "").strip()
        if not raw:
            return ["http://localhost:8001", "http://127.0.0.1:8001"]
        return [o.strip() for o in raw.split(",") if o.strip()]


@lru_cache
def get_settings() -> AdminSettings:
    return AdminSettings()
