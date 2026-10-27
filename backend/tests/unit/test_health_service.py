import ast
import inspect
from types import ModuleType

from calculate3d.modules.health import router, service


def test_db_status_is_ok_when_ping_succeeds() -> None:
    assert service.db_status(lambda: True) == "ok"


def test_db_status_is_down_when_ping_fails() -> None:
    assert service.db_status(lambda: False) == "down"


def _imported_names(module: ModuleType) -> set[str]:
    """Top-level packages plus full dotted names, incl. `from pkg import name` targets."""
    tree = ast.parse(inspect.getsource(module))
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported.add(alias.name.split(".")[0])
                imported.add(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
            imported.add(node.module)
            imported.update(f"{node.module}.{alias.name}" for alias in node.names)
    return imported


def test_health_service_does_not_import_fastapi_or_sqlalchemy() -> None:
    assert not _imported_names(service) & {"sqlalchemy", "fastapi"}


def test_health_router_does_not_import_repo() -> None:
    imported = _imported_names(router)

    assert "calculate3d.modules.health.repo" not in imported
