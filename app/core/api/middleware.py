"""CORS, request ID, security headers, rate limit."""
import time
import uuid
from fastapi import FastAPI, Request
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse

from app.core.config import get_settings

# Paths that are rate-limited (POST only). Limit: RATE_LIMIT_MAX per RATE_LIMIT_WINDOW_SEC per IP.
RATE_LIMIT_PATH_PREFIXES = (
    "/api/v1/auth/login",
    "/api/v1/auth/register",
    "/api/v1/subscriptions/contact",
    "/api/v1/webhooks/",
)
RATE_LIMIT_WINDOW_SEC = 60
RATE_LIMIT_MAX = 10

# In-memory store: (ip, path_key) -> (count, window_start). Prune old entries periodically.
_rate_limit_store: dict[tuple[str, str], tuple[int, float]] = {}
_rate_limit_last_prune: float = 0
PRUNE_INTERVAL_SEC = 120


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.scope.get("client"):
        return request.scope["client"][0]
    return "0.0.0.0"


def _prune_rate_limit_store() -> None:
    global _rate_limit_last_prune
    now = time.monotonic()
    if now - _rate_limit_last_prune < PRUNE_INTERVAL_SEC:
        return
    _rate_limit_last_prune = now
    cutoff = now - RATE_LIMIT_WINDOW_SEC
    to_del = [k for k, v in _rate_limit_store.items() if v[1] < cutoff]
    for k in to_del:
        del _rate_limit_store[k]


def _rate_limit_check(ip: str, path: str) -> bool:
    """True if request is within limit, False if over limit."""
    path_key = next((p for p in RATE_LIMIT_PATH_PREFIXES if path.rstrip("/").startswith(p.rstrip("/"))), path)
    key = (ip, path_key)
    now = time.monotonic()
    if key in _rate_limit_store:
        count, start = _rate_limit_store[key]
        if now - start >= RATE_LIMIT_WINDOW_SEC:
            _rate_limit_store[key] = (1, now)
            return True
        if count >= RATE_LIMIT_MAX:
            return False
        _rate_limit_store[key] = (count + 1, start)
        return True
    _rate_limit_store[key] = (1, now)
    return True


def setup_middleware(app: FastAPI, allowed_origins: list[str] | None = None) -> None:
    # With allow_credentials=True, never use allow_origins=["*"] (security policy).
    origins = allowed_origins if allowed_origins else ["http://localhost:8000", "http://127.0.0.1:8000"]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def rate_limit_and_headers(request: Request, call_next):
        # Rate limit: POST to auth/contact/webhook paths only
        if request.method == "POST":
            path = request.scope.get("path", "")
            if any(path.rstrip("/").startswith(p.rstrip("/")) for p in RATE_LIMIT_PATH_PREFIXES):
                _prune_rate_limit_store()
                ip = _client_ip(request)
                if not _rate_limit_check(ip, path):
                    return JSONResponse(
                        status_code=429,
                        content={"detail": "Too many requests. Try again later."},
                    )

        response = await call_next(request)

        # Security headers (policy: X-Content-Type-Options, X-Frame-Options, HSTS in production)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        settings = get_settings()
        if settings.is_production():
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        response.headers["X-Request-ID"] = request_id
        return response
