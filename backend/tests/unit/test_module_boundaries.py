import ast
from pathlib import Path

import pytest

MODULES = Path(__file__).resolve().parents[2] / "src" / "calculate3d" / "modules"
PREFIX = "calculate3d.modules."
PRIVATE = {"schemas", "repo", "tables", "router"}


def _foreign_private_imports(path: Path, own: str) -> list[str]:
    found: list[str] = []
    for node in ast.walk(ast.parse(path.read_text())):
        targets: list[str] = []
        if isinstance(node, ast.Import):
            targets = [a.name for a in node.names]
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            targets = [node.module] + [f"{node.module}.{a.name}" for a in node.names]
        for t in targets:
            parts = t.removeprefix(PREFIX).split(".")
            if t.startswith(PREFIX) and parts[0] != own and len(parts) > 1 and parts[1] in PRIVATE:
                found.append(t)
    return sorted(set(found))


@pytest.mark.parametrize(
    "source",
    sorted(MODULES.glob("*/*.py")),
    ids=lambda p: f"{p.parent.name}/{p.name}",
)
def test_modules_import_only_the_service_of_other_modules(source: Path) -> None:
    assert _foreign_private_imports(source, source.parent.name) == []
