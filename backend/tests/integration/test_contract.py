"""The running app's OpenAPI covers docs/features/cost-calculator/contracts/openapi.yaml."""

import inspect
from collections.abc import Iterator
from typing import Any

import pytest
import yaml
from fastapi.testclient import TestClient

import calculate3d.modules.catalog.service
import calculate3d.modules.costing.service
import calculate3d.modules.importing.service
import calculate3d.modules.pricing.service  # noqa: F401 — register every AppError subclass
from calculate3d.core.config import REPO_DIR
from calculate3d.core.errors import AppError

CONTRACT_PATH = REPO_DIR / "docs" / "features" / "cost-calculator" / "contracts" / "openapi.yaml"
CONTRACT: dict[str, Any] = yaml.safe_load(CONTRACT_PATH.read_text())
# print-file-import is a delta contract: only the operations that feature adds or changes.
IMPORT_CONTRACT_PATH = (
    REPO_DIR / "docs" / "features" / "print-file-import" / "contracts" / "openapi.yaml"
)
IMPORT_CONTRACT: dict[str, Any] = yaml.safe_load(IMPORT_CONTRACT_PATH.read_text())
METHODS = {"get", "post", "put", "patch", "delete"}
# Cross-cutting codes rendered by core/errors.py and core/guard.py (not AppError subclasses).
CORE_CODES = {
    "validation_error",
    "internal_error",
    "host_not_allowed",
    "cross_origin_forbidden",
    "unsupported_media_type",
}


def _contract_operations(contract: dict[str, Any] = CONTRACT) -> list[tuple[str, str]]:
    return [
        (path, method)
        for path, item in contract["paths"].items()
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


def _contract_codes(contract: dict[str, Any] = CONTRACT) -> set[str]:
    codes = set()
    for node in _walk(contract):
        if isinstance(node, dict) and isinstance(node.get("code"), str):
            codes.add(node["code"])
        if isinstance(node, dict) and isinstance(node.get("code"), dict):
            codes.add(node["code"].get("const"))
            codes.update(node["code"].get("enum", []))
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


@pytest.mark.parametrize(
    ("contract", "path", "method"),
    [
        pytest.param(contract, path, method, id=f"{name}:{method} {path}")
        for name, contract in (("cost-calculator", CONTRACT), ("import", IMPORT_CONTRACT))
        for path, method in _contract_operations(contract)
    ],
)
def test_every_contract_operation_exists_with_its_error_responses(
    app_openapi: dict[str, Any], contract: dict[str, Any], path: str, method: str
) -> None:
    expected = contract["paths"][path][method]
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

    contract_ops = set(_contract_operations()) | set(_contract_operations(IMPORT_CONTRACT))
    assert actual - contract_ops == {("/api/health", "get")}


def test_error_code_registry_matches_the_contract() -> None:
    contract_codes = _contract_codes()
    registry = _app_error_codes() | CORE_CODES

    assert len(contract_codes) == 13
    # One registry for both feature contracts: every advertised code exists, and nothing more.
    assert registry == contract_codes | _contract_codes(IMPORT_CONTRACT)


# ── schema-level fidelity (T23, review findings S1-4 / S1-5) ──
# The contract is the target: only keywords the CONTRACT states are compared; the live spec may add
# titles, descriptions, examples. Every divergence is collected so one run shows the whole gap.

_SCALAR_KEYWORDS = (
    "format",
    "minLength",
    "maxLength",
    "pattern",
    "multipleOf",
    "minItems",
    "maxItems",
    "uniqueItems",
    "enum",
)


def _resolve(spec: dict[str, Any], node: dict[str, Any]) -> dict[str, Any]:
    """Follow `$ref`s and merge `allOf`; `ref` siblings (3.1) override the target."""
    if "$ref" in node:
        target: Any = spec
        for part in node["$ref"].removeprefix("#/").split("/"):
            target = target[part]
        node = {**_resolve(spec, target), **{k: v for k, v in node.items() if k != "$ref"}}
    if "allOf" in node:
        merged: dict[str, Any] = {k: v for k, v in node.items() if k != "allOf"}
        for part in node["allOf"]:
            sub = _resolve(spec, part)
            merged["properties"] = {**merged.get("properties", {}), **sub.get("properties", {})}
            merged["required"] = [*merged.get("required", []), *sub.get("required", [])]
            for key, value in sub.items():
                if key not in ("properties", "required"):
                    merged.setdefault(key, value)
        node = merged
    return node


def _normalise(spec: dict[str, Any], node: dict[str, Any]) -> dict[str, Any]:
    """Reduce 3.1 `type: [x, null]` and pydantic `anyOf` with null to one comparable form."""
    node = _resolve(spec, node)
    types: set[str] = set()
    raw = node.get("type")
    if isinstance(raw, list):
        types.update(raw)
    elif isinstance(raw, str):
        types.add(raw)
    out = {k: v for k, v in node.items() if k not in ("anyOf", "type")}
    variants = node.get("anyOf")
    if variants:
        non_null = []
        for variant in variants:
            if variant.get("type") == "null":
                types.add("null")
            else:
                non_null.append(_normalise(spec, variant))
        if len(non_null) == 1:
            inner = non_null[0]
            types |= set(inner.get("_types", ()))
            out = {**{k: v for k, v in inner.items() if k != "_types"}, **out}
        else:
            for variant in non_null:
                types |= set(variant.get("_types", ()))
    out["_types"] = sorted(types)
    return out


def _int_bounds(node: dict[str, Any]) -> tuple[int | None, int | None]:
    """Effective inclusive integer bounds: `exclusiveMinimum: 0` == `minimum: 1`."""
    low, high = node.get("minimum"), node.get("maximum")
    if "exclusiveMinimum" in node:
        low = max(filter(None.__ne__, [low, node["exclusiveMinimum"] + 1]))
    if "exclusiveMaximum" in node:
        high = min(filter(None.__ne__, [high, node["exclusiveMaximum"] - 1]))
    return low, high


def _diff(
    path: str,
    c_spec: dict[str, Any],
    l_spec: dict[str, Any],
    c_raw: dict[str, Any],
    l_raw: dict[str, Any],
) -> list[str]:
    contract, live = _normalise(c_spec, c_raw), _normalise(l_spec, l_raw)
    found: list[str] = []

    def compare(what: str, expected: Any, actual: Any) -> None:
        if expected != actual:
            found.append(f"{path}{what}: contract {expected!r} vs live {actual!r}")

    if contract["_types"]:
        compare(" type", contract["_types"], live["_types"])
    if "integer" in contract["_types"]:
        c_bounds, l_bounds = _int_bounds(contract), _int_bounds(live)
        if c_bounds[0] is not None:
            compare(" minimum", c_bounds[0], l_bounds[0])
        if c_bounds[1] is not None:
            compare(" maximum", c_bounds[1], l_bounds[1])
    for keyword in _SCALAR_KEYWORDS:
        if keyword in contract:
            compare(f" {keyword}", contract[keyword], live.get(keyword))
    if contract.get("additionalProperties") is False:
        compare(" additionalProperties", False, live.get("additionalProperties"))
    if "required" in contract or "properties" in contract:
        compare(
            " required",
            sorted(set(contract.get("required", []))),
            sorted(set(live.get("required", []))),
        )
    for name, c_prop in contract.get("properties", {}).items():
        if name not in live.get("properties", {}):
            found.append(f"{path}.{name}: contract defines it vs live missing")
            continue
        found += _diff(f"{path}.{name}", c_spec, l_spec, c_prop, live["properties"][name])
    if isinstance(contract.get("items"), dict):
        if isinstance(live.get("items"), dict):
            found += _diff(f"{path}[]", c_spec, l_spec, contract["items"], live["items"])
        else:
            found.append(f"{path}[]: contract has items vs live none")
    return found


def _shared_schema_names(live: dict[str, Any]) -> list[str]:
    return sorted(set(CONTRACT["components"]["schemas"]) & set(live["components"]["schemas"]))


@pytest.mark.parametrize("name", sorted(CONTRACT["components"]["schemas"]))
def test_live_schema_matches_the_contract_schema(app_openapi: dict[str, Any], name: str) -> None:
    if name not in app_openapi["components"]["schemas"]:
        pytest.skip(f"{name} is not a named schema in the live spec")

    divergences = _diff(
        name,
        CONTRACT,
        app_openapi,
        {"$ref": f"#/components/schemas/{name}"},
        {"$ref": f"#/components/schemas/{name}"},
    )

    assert not divergences, "\n" + "\n".join(divergences)


# The parse result, its problems (D3) and catalog's changed input (ADR 0003).
IMPORT_SCHEMAS = (
    "ItemInput",
    "FilamentMappingInput",
    "SlicerFile",
    "SlicedPlate",
    "SlicerFilament",
    "ImportSettingsMissingProblem",
    "ImportRejectedProblem",
)


@pytest.mark.parametrize("name", IMPORT_SCHEMAS)
def test_live_import_schema_matches_the_import_contract(
    app_openapi: dict[str, Any], name: str
) -> None:
    assert name in app_openapi["components"]["schemas"], f"{name} is not in the live spec"
    divergences = _diff(
        name,
        IMPORT_CONTRACT,
        app_openapi,
        {"$ref": f"#/components/schemas/{name}"},
        {"$ref": f"#/components/schemas/{name}"},
    )

    assert not divergences, "\n" + "\n".join(divergences)


def test_most_contract_schemas_are_compared_not_skipped(app_openapi: dict[str, Any]) -> None:
    shared = _shared_schema_names(app_openapi)

    for name in ("Plastic", "PlasticInput", "PriceSettings", "Quote", "Item", "ItemSummary"):
        assert name in shared, f"{name} must exist in both specs so it is actually compared"


def _path_id_params(spec: dict[str, Any], path: str, method: str) -> dict[str, dict[str, Any]]:
    """Path-item-level and operation-level parameters merged; operation wins by (name, in)."""
    item = spec["paths"][path]
    merged: dict[tuple[str, str], dict[str, Any]] = {}
    for raw in [*item.get("parameters", []), *item[method].get("parameters", [])]:
        param = _resolve(spec, raw)
        merged[(param["name"], param["in"])] = param
    return {
        name: _normalise(spec, param["schema"])
        for (name, location), param in merged.items()
        if location == "path" and (name == "id" or name.endswith("_id"))
    }


@pytest.mark.parametrize(("path", "method"), _contract_operations())
def test_id_path_parameters_keep_the_contract_uuid_format(
    app_openapi: dict[str, Any], path: str, method: str
) -> None:
    contract_params = _path_id_params(CONTRACT, path, method)
    live_params = _path_id_params(app_openapi, path, method)

    if "{" in path:  # never vacuous: a templated path must yield contract id params
        assert contract_params, f"{method.upper()} {path}: no path id parameter read from contract"
        assert set(contract_params) <= set(live_params), f"{path} {method}: live lacks id params"
    divergences = [
        f"{path} {method} path param {name}: contract "
        f"type/format {c['_types']!r}/{c.get('format')!r} vs live "
        f"{live_params.get(name, {}).get('_types')!r}/{live_params.get(name, {}).get('format')!r}"
        for name, c in contract_params.items()
        if (c["_types"], c.get("format"))
        != (live_params[name]["_types"], live_params[name].get("format"))
    ]
    assert not divergences, "\n" + "\n".join(divergences)


@pytest.mark.parametrize("operation_id", ["deletePlastic", "deleteItem"])
def test_delete_operations_declare_415_problem_json(
    app_openapi: dict[str, Any], operation_id: str
) -> None:
    for label, spec in (("contract", CONTRACT), ("live", app_openapi)):
        operation = next(
            op
            for item in spec["paths"].values()
            for method, op in item.items()
            if method in METHODS and op["operationId"] == operation_id
        )
        response = operation["responses"].get("415")

        assert response is not None, f"{label}: {operation_id} declares no 415"
        content = _resolve(spec, response)["content"]
        assert "application/problem+json" in content, f"{label}: {operation_id} 415 content"
