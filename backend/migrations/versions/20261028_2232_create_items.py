"""create items

Promoted verbatim from docs/features/cost-calculator/migrations/20261028120002_create_items.{up,down}.sql.

Revision ID: 926547211482
Revises: f0cceb19344b
Create Date: 2026-10-28 22:32:00
"""

from alembic import op

revision: str = "926547211482"
down_revision: str | None = "f0cceb19344b"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.execute("""
-- catalog: вироби — лише параметри, ніколи не ціна (US-04..06, ADR 0003).
-- name / name_key — як у plastics (ADR 0006).
CREATE TABLE IF NOT EXISTS items (
    id           TEXT    NOT NULL PRIMARY KEY,
    name         TEXT    NOT NULL,
    name_key     TEXT    NOT NULL,
    print_time_s INTEGER NOT NULL,
    created_at   TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);
""")
    op.execute("""
CREATE UNIQUE INDEX IF NOT EXISTS uq_items_name_key ON items (name_key);
""")


def downgrade() -> None:
    op.execute("""
DROP INDEX IF EXISTS uq_items_name_key;
""")
    op.execute("""
DROP TABLE IF EXISTS items;
""")
