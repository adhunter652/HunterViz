"""CORS, request ID, rate limit."""
import uuid

from fastapi import FastAPI, Request
from starlette.middleware.cors import CORSMiddleware


def setup_middleware(app: FastAPI, allowed_origins: list[str] | None = None) -> None:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins or ["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def add_request_id(request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response
