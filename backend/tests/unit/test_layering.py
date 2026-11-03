import ast
from pathlib import Path

import pytest

MODULES = Path(__file__).resolve().parents[2] / "src" / "calculate3d" / "modules"
FORBIDDEN = ("fastapi", "starlette", "sqlalchemy")


def _imported_roots(path: Path) -> set[str]:
    roots: set[str] = set()
    for node in ast.walk(ast.parse(path.read_text())):
        if isinstance(node, ast.Import):
            roots |= {alias.name.split(".")[0] for alias in node.names}
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            roots.add(node.module.split(".")[0])
    return roots


@pytest.mark.parametrize(
    "service", sorted(MODULES.glob("*/service.py")), ids=lambda p: p.parent.name
)
def test_services_import_no_web_or_sql_framework(service: Path) -> None:
    assert not _imported_roots(service) & set(FORBIDDEN)
