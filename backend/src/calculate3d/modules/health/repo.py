"""Health persistence — takes the Engine, not the per-request Connection.

The request transaction (`get_connection`) opens before the handler runs, so an unreachable
database would fail the request; health must report `down` instead.
"""

from sqlalchemy import Engine, text
from sqlalchemy.exc import SQLAlchemyError

# Lets the service type the engine without importing SQLAlchemy.
DbEngine = Engine


def ping(engine: Engine) -> bool:
    try:
        # Deferred begin: the ping must not take the write lock (see core/db.py).
        with engine.connect().execution_options(deferred_begin=True) as conn:
            return conn.execute(text("SELECT 1")).scalar() == 1
    except SQLAlchemyError:
        return False
