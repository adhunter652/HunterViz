"""JSON file-backed SubscriptionRepository."""
import json
from pathlib import Path
from typing import Optional

from app.core.application.ports import SubscriptionRepository
from app.core.config import get_settings
from app.core.domain.value_objects import UserId
from app.core.infrastructure.gcs_sync import push_data_file


class JsonSubscriptionStore(SubscriptionRepository):
    def __init__(self, file_path: str):
        self._path = Path(file_path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        if not self._path.exists():
            self._write({"subscriptions": []})

    def _read(self) -> dict:
        with open(self._path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _write(self, data: dict) -> None:
        tmp = self._path.with_suffix(self._path.suffix + ".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        tmp.replace(self._path)
        push_data_file(get_settings(), self._path)

    def get_active_by_user_id(self, user_id: UserId) -> Optional[dict]:
        data = self._read()
        for s in data.get("subscriptions", []):
            if s.get("user_id") == str(user_id) and s.get("status") == "active":
                return s
        return None

    def save(self, subscription: dict) -> None:
        data = self._read()
        subs = data.get("subscriptions", [])
        sid = subscription.get("id") or subscription.get("user_id")
        for i, s in enumerate(subs):
            if s.get("user_id") == subscription.get("user_id"):
                subs[i] = subscription
                data["subscriptions"] = subs
                self._write(data)
                return
        subs.append(subscription)
        data["subscriptions"] = subs
        self._write(data)
