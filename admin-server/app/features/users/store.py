"""JSON user store. Same file path and GCS blob as main app; preserves all keys (e.g. dashboards, password_hash)."""
import json
from pathlib import Path
from typing import Optional

from app.core.config import get_settings
from app.core.infrastructure.gcs_sync import push_data_file


class UserStore:
    def __init__(self, file_path: str):
        self._path = Path(file_path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        if not self._path.exists():
            self._write({"users": []})

    def _read(self) -> dict:
        with open(self._path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _write(self, data: dict) -> None:
        tmp = self._path.with_suffix(self._path.suffix + ".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        tmp.replace(self._path)
        push_data_file(get_settings(), self._path)

    def list_users(self) -> list[dict]:
        """Return all users. Each dict may include id, email, company_name, stripe_customer_id, created_at, dashboards, etc. Exclude password_hash from list view."""
        data = self._read()
        out = []
        for u in data.get("users", []):
            u_copy = {k: v for k, v in u.items() if k != "password_hash"}
            out.append(u_copy)
        return out

    def get_by_id(self, user_id: str) -> Optional[dict]:
        """Return full user dict (including password_hash) for in-app merge on update. Caller must not log or expose password_hash."""
        data = self._read()
        for u in data.get("users", []):
            if u.get("id") == user_id:
                return dict(u)
        return None

    def save(self, user: dict) -> None:
        """Save user. Pass full user dict so password_hash and other keys are preserved."""
        data = self._read()
        users = data.get("users", [])
        uid = user.get("id")
        for i, u in enumerate(users):
            if u.get("id") == uid:
                users[i] = user
                data["users"] = users
                self._write(data)
                return
        users.append(user)
        data["users"] = users
        self._write(data)
