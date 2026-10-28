"""OpenAPI side of the problem+json envelope: body models and `responses=` helpers.

`core/errors.py` renders the bodies; these models only document them so the generated web
types know every error shape (`.claude/rules/openapi.md` § Repo adaptation).
"""

from typing import Any

from fastapi import FastAPI
from pydantic import BaseModel

from calculate3d.core.errors import PROBLEM_JSON


class Problem(BaseModel):
    type: str
    title: str
    status: int
    detail: str
    code: str


class ValidationIssue(BaseModel):
    loc: list[str | int]
    msg: str


class ValidationProblem(Problem):
    errors: list[ValidationIssue]


class FieldProblem(Problem):
    field: str


def problem_response(model: type[Problem], description: str) -> dict[str, Any]:
    return {"model": model, "description": description}


VALIDATION_ERROR = problem_response(
    ValidationProblem, "Тіло чи параметри не пройшли перевірку типів і меж"
)
UNSUPPORTED_MEDIA_TYPE = problem_response(
    Problem, "Змінний запит не у форматі application/json (ADR 0007)"
)
# Every /api operation can meet the request guard and an unexpected failure.
GUARD_RESPONSES: dict[int | str, dict[str, Any]] = {
    400: problem_response(Problem, "Host поза переліком дозволених (AC-16, ADR 0007)"),
    403: problem_response(Problem, "Запит зі стороннього сайту (AC-16b, ADR 0007)"),
    500: problem_response(Problem, "Неочікувана помилка сервера"),
}


def use_problem_json_in_openapi(app: FastAPI) -> None:
    """Post-process FastAPI's OpenAPI so it matches what `core/errors.py` actually sends.

    - `responses=` models land under application/json; errors are application/problem+json.
    - FastAPI adds a default 422 (`HTTPValidationError`) to operations that declare none —
      e.g. a plain `str` path id that cannot fail; real 422s are declared via VALIDATION_ERROR.
    """
    generate = app.openapi

    def openapi() -> dict[str, Any]:
        if app.openapi_schema is None:
            schema = generate()
            for path in schema.get("paths", {}).values():
                for operation in path.values():
                    _rewrite_error_responses(operation.get("responses", {}))
            components = schema.get("components", {}).get("schemas", {})
            for name in ("HTTPValidationError", "ValidationError"):
                components.pop(name, None)
        return app.openapi_schema or generate()

    app.openapi = openapi  # type: ignore[method-assign]


def _rewrite_error_responses(responses: dict[str, Any]) -> None:
    for status in list(responses):
        content = responses[status].get("content", {})
        json_content = content.get("application/json", {})
        if json_content.get("schema", {}).get("$ref", "").endswith("/HTTPValidationError"):
            del responses[status]
        elif status[0] in "45" and json_content:
            responses[status]["content"] = {PROBLEM_JSON: json_content}
