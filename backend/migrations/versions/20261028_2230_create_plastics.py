"""create plastics

Promoted verbatim from docs/features/cost-calculator/migrations/20261028120000_create_plastics.{up,down}.sql.

Revision ID: c9e56039bfdc
Revises: 0a1b2c3d4e5f
Create Date: 2026-10-28 22:30:00
"""

from alembic import op

revision: str = "c9e56039bfdc"
down_revision: str | None = "0a1b2c3d4e5f"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.execute("""
-- pricing: пластики з поточною ціною за кілограм (US-01, AC-01..03).
-- name — як ввів автор, без пробілів на краях; name_key = casefold(name) рахує застосунок (ADR 0006).
CREATE TABLE IF NOT EXISTS plastics (
    id               TEXT    NOT NULL PRIMARY KEY,
    name             TEXT    NOT NULL,
    name_key         TEXT    NOT NULL,
    price_per_kg_kop INTEGER NOT NULL,
    created_at       TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);
""")
    op.execute("""
CREATE UNIQUE INDEX IF NOT EXISTS uq_plastics_name_key ON plastics (name_key);
""")


def downgrade() -> None:
    op.execute("""
DROP INDEX IF EXISTS uq_plastics_name_key;
""")
    op.execute("""
DROP TABLE IF EXISTS plastics;
""")
