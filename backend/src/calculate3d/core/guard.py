"""Request guard (cost-calculator ADR 0007): Host allowlist, same-origin `/api`, JSON-only writes.

One exception (print-file-import ADR 0002): `POST /api/importing/parse` takes only a raw
`application/octet-stream` body — the slicer file — and nothing else; Host and origin checks
stay the same for it.

A pure ASGI middleware, so a rejected request never reaches routing or opens a DB transaction.
"""

from starlette.datastructures import Headers
from starlette.types import ASGIApp, Receive, Scope, Send

from calculate3d.core.errors import problem

MUTATING_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})
CROSS_SITE = frozenset({"cross-site", "same-site"})
JSON = "application/json"
OCTET_STREAM = "application/octet-stream"
IMPORT_ROUTE = ("POST", "/api/importing/parse")


def _is_api(path: str) -> bool:
    return path == "/api" or path.startswith("/api/")


def _declares_body(headers: Headers) -> bool:
    # An empty HTML form still sends a Content-Type, so it counts as a body.
    return (
        headers.get("content-length", "0") != "0"
        or "transfer-encoding" in headers
        or "content-type" in headers
    )


def _media_type(headers: Headers) -> str:
    return headers.get("content-type", "").split(";", 1)[0].strip().lower()


def _required_media_type(scope: Scope) -> str:
    return OCTET_STREAM if (scope["method"], scope["path"]) == IMPORT_ROUTE else JSON


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
                and _media_type(headers) != (required := _required_media_type(scope))
            ):
                response = problem(
                    415, f"Content-Type must be {required}", "unsupported_media_type"
                )
        if response is not None:
            await response(scope, receive, send)
            return
        await self.app(scope, receive, send)
