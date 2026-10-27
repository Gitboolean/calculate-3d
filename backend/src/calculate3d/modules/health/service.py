"""Health checks — no FastAPI imports, so it stays unit-testable."""

from sqlalchemy import Connection, text


def database_ok(conn: Connection) -> bool:
    return conn.execute(text("SELECT 1")).scalar() == 1
