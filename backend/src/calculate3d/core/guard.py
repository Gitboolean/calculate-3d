"""Request guard (cost-calculator ADR 0007): Host allowlist, same-origin `/api`, JSON-only writes.

A pure ASGI middleware, so a rejected request never reaches routing or opens a DB transaction.
"""

from starlette.datastructures import Headers
from starlette.types import ASGIApp, Receive, Scope, Send

from calculate3d.core.errors import problem

MUTATING_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})
CROSS_SITE = frozenset({"cross-site", "same-site"})


def _is_api(path: str) -> bool:
    return path == "/api" or path.startswith("/api/")


def _declares_body(headers: Headers) -> bool:
    # An empty HTML form still sends a Content-Type, so it counts as a body.
    return (
        headers.get("content-length", "0") != "0"
        or "transfer-encoding" in headers
        or "content-type" in headers
    )


def _is_json(headers: Headers) -> bool:
    media_type = headers.get("content-type", "").split(";", 1)[0].strip().lower()
    return media_type == "application/json"


class RequestGuard:
    def __init__(
        self, app: ASGIApp, *, allowed_hosts: frozenset[str], allowed_origins: frozenset[str]
    ) -> None:
        self.app = app
        self.allowed_hosts = allowed_hosts
        self.allowed_origins = allowed_origins

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        headers = Headers(scope=scope)
        response = None
        if headers.get("host", "") not in self.allowed_hosts:
            response = problem(400, "Host is not allowed", "host_not_allowed")
        elif _is_api(scope["path"]):
            origin = headers.get("origin")
            if headers.get("sec-fetch-site") in CROSS_SITE or (
                origin is not None and origin not in self.allowed_origins
            ):
                response = problem(
                    403, "Cross-origin request is forbidden", "cross_origin_forbidden"
                )
            elif (
                scope["method"] in MUTATING_METHODS
                and _declares_body(headers)
                and not _is_json(headers)
            ):
                response = problem(
                    415, "Content-Type must be application/json", "unsupported_media_type"
                )
        if response is not None:
            await response(scope, receive, send)
            return
        await self.app(scope, receive, send)
