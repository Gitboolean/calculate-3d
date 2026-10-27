import ast
import inspect

from calculate3d.modules.health import service


def test_db_status_is_ok_when_ping_succeeds() -> None:
    assert service.db_status(lambda: True) == "ok"


def test_db_status_is_down_when_ping_fails() -> None:
    assert service.db_status(lambda: False) == "down"


def test_health_service_does_not_import_fastapi_or_sqlalchemy() -> None:
    tree = ast.parse(inspect.getsource(service))
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])

    assert not imported & {"sqlalchemy", "fastapi"}
