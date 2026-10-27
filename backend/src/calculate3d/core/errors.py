"""Domain errors and the RFC 9457 problem+json envelope used for every error response."""

from collections.abc import Mapping
from http import HTTPStatus

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

PROBLEM_JSON = "application/problem+json"


class AppError(Exception):
    """Base for domain errors; services raise subclasses, never HTTPException."""

    def __init__(self, code: str, message: str, status: int = 400) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status = status


def _phrase(status: int) -> str:
    try:
        return HTTPStatus(status).phrase
    except ValueError:
        return "Error"


def problem(
    status: int,
    detail: str,
    code: str,
    *,
    headers: Mapping[str, str] | None = None,
    **extra: object,
) -> JSONResponse:
    body: dict[str, object] = {
        "type": "about:blank",
        "title": _phrase(status),
        "status": status,
        "detail": detail,
        "code": code,
        **extra,
    }
    return JSONResponse(body, status_code=status, headers=headers, media_type=PROBLEM_JSON)


async def _app_error(_: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, AppError)
    return problem(exc.status, exc.message, exc.code)


async def _http_error(_: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, StarletteHTTPException)
    try:
        code = HTTPStatus(exc.status_code).name.lower()
    except ValueError:
        code = "http_error"
    return problem(exc.status_code, str(exc.detail), code, headers=exc.headers)


async def _unhandled_error(_: Request, __: Exception) -> JSONResponse:
    return problem(500, "Internal server error", "internal_error")


async def _validation_error(_: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, RequestValidationError)
    errors = [{"loc": list(e["loc"]), "msg": e["msg"]} for e in exc.errors()]
    return problem(422, "Request validation failed", "validation_error", errors=errors)


def register_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AppError, _app_error)
    app.add_exception_handler(StarletteHTTPException, _http_error)
    app.add_exception_handler(RequestValidationError, _validation_error)
    app.add_exception_handler(Exception, _unhandled_error)
