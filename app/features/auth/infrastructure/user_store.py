"""JSON file-backed UserRepository."""
import json
import os
from pathlib import Path
from typing import Optional

from app.core.application.ports import UserRepository
from app.core.domain.value_objects import Email, UserId


class JsonUserStore(UserRepository):
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

    def get_by_id(self, user_id: UserId) -> Optional[dict]:
        data = self._read()
        for u in data.get("users", []):
            if u.get("id") == str(user_id):
                out = {k: v for k, v in u.items() if k != "password_hash"}
                return out
        return None

    def get_by_email(self, email: Email) -> Optional[dict]:
        data = self._read()
        for u in data.get("users", []):
            if (u.get("email") or "").lower() == str(email).lower():
                return dict(u)
        return None

    def save(self, user: dict) -> None:
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
