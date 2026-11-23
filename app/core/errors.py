"""Centralized error model. Every error leaves the API as

    {"error": {"code", "message", "retryable", "request_id", "details"}}

matching the KB tool contract ({error_code, message, retryable}). Internal
exception text is never sent to clients."""
from __future__ import annotations

from typing import Any

import structlog
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.request_context import get_request_id

log = structlog.get_logger(__name__)


class AppError(Exception):
    status_code = 500
    code = "INTERNAL_ERROR"
    retryable = False

    def __init__(
        self,
        message: str,
        *,
        code: str | None = None,
        details: dict[str, Any] | None = None,
        status_code: int | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        if code:
            self.code = code
        if status_code:
            self.status_code = status_code
        self.details = details or {}
        self.headers = headers or {}


class BadRequestError(AppError):
    status_code, code = 400, "BAD_REQUEST"


class AuthenticationError(AppError):
    status_code, code = 401, "UNAUTHENTICATED"


class PermissionDeniedError(AppError):
    status_code, code = 403, "FORBIDDEN"


class NotFoundError(AppError):
    status_code, code = 404, "NOT_FOUND"


class ConflictError(AppError):
    status_code, code, retryable = 409, "CONFLICT", True


class BusinessRuleError(AppError):
    """A request that is well-formed but not allowed by policy (422)."""

    status_code, code = 422, "BUSINESS_RULE_VIOLATION"


class RateLimitedError(AppError):
    status_code, code, retryable = 429, "RATE_LIMITED", True


class DependencyUnavailableError(AppError):
    status_code, code, retryable = 503, "DEPENDENCY_UNAVAILABLE", True


def error_body(code: str, message: str, retryable: bool, details: dict[str, Any] | None = None) -> dict:
    return {
        "error": {
            "code": code,
            "message": message,
            "retryable": retryable,
            "request_id": get_request_id(),
            "details": details or {},
        }
    }


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def _app_error(_: Request, exc: AppError) -> JSONResponse:
        if exc.status_code >= 500:
            log.error("app_error", code=exc.code, error=exc.message)
        else:
            log.info("request_rejected", code=exc.code, status=exc.status_code)
        return JSONResponse(
            status_code=exc.status_code,
            content=error_body(exc.code, exc.message, exc.retryable, exc.details),
            headers=exc.headers,
        )

    @app.exception_handler(RequestValidationError)
    async def _validation(_: Request, exc: RequestValidationError) -> JSONResponse:
        # Only location + message + type: never echo the submitted input back.
        issues = [
            {"loc": [str(p) for p in e.get("loc", ())], "msg": e.get("msg"), "type": e.get("type")}
            for e in exc.errors()
        ]
        return JSONResponse(
            status_code=422,
            content=error_body("VALIDATION_ERROR", "Request validation failed", False, {"issues": issues}),
        )

    @app.exception_handler(StarletteHTTPException)
    async def _http(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        code = {404: "NOT_FOUND", 405: "METHOD_NOT_ALLOWED"}.get(exc.status_code, "HTTP_ERROR")
        return JSONResponse(
            status_code=exc.status_code,
            content=error_body(code, str(exc.detail), exc.status_code >= 500),
            headers=getattr(exc, "headers", None),
        )

    @app.exception_handler(Exception)
    async def _unhandled(_: Request, exc: Exception) -> JSONResponse:
        log.exception("unhandled_exception", error_type=type(exc).__name__)
        return JSONResponse(
            status_code=500,
            content=error_body("INTERNAL_ERROR", "An unexpected error occurred", True),
        )
