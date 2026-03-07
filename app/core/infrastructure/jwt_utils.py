"""JWT decode only (issuing is in auth feature)."""
import jwt
from typing import Any, Optional


def decode_token(token: str, secret_key: str) -> Optional[dict[str, Any]]:
    try:
        payload = jwt.decode(
            token,
            secret_key,
            algorithms=["HS256"],
            options={"verify_exp": True},
        )
        return payload
    except Exception:
        return None
