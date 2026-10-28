"""The running app's OpenAPI covers docs/features/cost-calculator/contracts/openapi.yaml."""

import inspect
from collections.abc import Iterator
from typing import Any

import pytest
import yaml
from fastapi.testclient import TestClient

import calculate3d.modules.catalog.service
import calculate3d.modules.costing.service
import calculate3d.modules.pricing.service  # noqa: F401 — register every AppError subclass
from calculate3d.core.config import REPO_DIR
from calculate3d.core.errors import AppError

CONTRACT_PATH = REPO_DIR / "docs" / "features" / "cost-calculator" / "contracts" / "openapi.yaml"
CONTRACT: dict[str, Any] = yaml.safe_load(CONTRACT_PATH.read_text())
METHODS = {"get", "post", "put", "patch", "delete"}
# Cross-cutting codes rendered by core/errors.py and core/guard.py (not AppError subclasses).
CORE_CODES = {
    "validation_error",
    "internal_error",
    "host_not_allowed",
    "cross_origin_forbidden",
    "unsupported_media_type",
}


def _contract_operations() -> list[tuple[str, str]]:
    return [
        (path, method)
        for path, item in CONTRACT["paths"].items()
        for method in item
        if method in METHODS
    ]


def _walk(node: Any) -> Iterator[Any]:
    yield node
    if isinstance(node, dict):
        for value in node.values():
            yield from _walk(value)
    elif isinstance(node, list):
        for value in node:
            yield from _walk(value)


def _contract_codes() -> set[str]:
    codes = set()
    for node in _walk(CONTRACT):
        if isinstance(node, dict) and isinstance(node.get("code"), str):
            codes.add(node["code"])
        if isinstance(node, dict) and isinstance(node.get("code"), dict):
            codes.add(node["code"].get("const"))
    return codes - {None}


def _app_error_codes() -> set[str]:
    codes = set()
    pending = list(AppError.__subclasses__())
    while pending:
        cls = pending.pop()
        pending.extend(cls.__subclasses__())
        params = list(inspect.signature(cls).parameters.values())
        args = [[] if "list" in str(p.annotation) else 0 for p in params]
        codes.add(cls(*args).code)
    return codes


@pytest.fixture(scope="module")
def app_openapi(migrated_db_template: Any) -> dict[str, Any]:
    from calculate3d.core.config import Settings
    from calculate3d.main import create_app

    app = create_app(Settings(database_url=f"sqlite:///{migrated_db_template}"))
    with TestClient(app) as client:
        schema: dict[str, Any] = client.get("/openapi.json").json()
    return schema


@pytest.mark.parametrize(("path", "method"), _contract_operations())
def test_every_contract_operation_exists_with_its_error_responses(
    app_openapi: dict[str, Any], path: str, method: str
) -> None:
    expected = CONTRACT["paths"][path][method]
    actual = app_openapi["paths"].get(path, {}).get(method)

    assert actual is not None, f"{method.upper()} {path} is missing"
    assert actual["operationId"] == expected["operationId"]
    expected_statuses = set(expected["responses"])
    assert expected_statuses <= set(actual["responses"]), expected["operationId"]
    for status in expected_statuses:
        if status[0] in "45":
            assert "application/problem+json" in actual["responses"][status]["content"]


def test_app_declares_no_operation_beyond_the_contract_and_health(
    app_openapi: dict[str, Any],
) -> None:
    actual = {(p, m) for p, item in app_openapi["paths"].items() for m in item if m in METHODS}

    assert actual - set(_contract_operations()) == {("/api/health", "get")}


def test_error_code_registry_matches_the_contract() -> None:
    contract_codes = _contract_codes()

    assert len(contract_codes) == 13
    assert _app_error_codes() | CORE_CODES == contract_codes
