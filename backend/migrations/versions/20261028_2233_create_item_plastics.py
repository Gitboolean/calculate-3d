"""create item plastics

Promoted verbatim from docs/features/cost-calculator/migrations/20261028120003_create_item_plastics.{up,down}.sql.

Revision ID: 65f15a51514f
Revises: 926547211482
Create Date: 2026-10-28 22:33:00
"""

from alembic import op

revision: str = "65f15a51514f"
down_revision: str | None = "926547211482"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.execute("""
-- catalog: витрата кожного пластику виробу (AC-06b, AC-07, AC-10, AC-14b).
-- PK (item_id, plastic_id) — один рядок на пластик у виробі; його ліва колонка індексує FK item_id.
-- Видалення виробу каскадно прибирає рядки (AC-15); пластик, який хтось використовує, видалити
-- не можна — RESTRICT страхує перевірку в pricing.service (AC-03, ADR 0005).
CREATE TABLE IF NOT EXISTS item_plastics (
    item_id    TEXT    NOT NULL REFERENCES items (id) ON DELETE CASCADE,
    plastic_id TEXT    NOT NULL REFERENCES plastics (id) ON DELETE RESTRICT,
    usage_cg   INTEGER NOT NULL,
    created_at TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    PRIMARY KEY (item_id, plastic_id)
);
""")
    op.execute("""
CREATE INDEX IF NOT EXISTS idx_item_plastics_plastic_id ON item_plastics (plastic_id);
""")


def downgrade() -> None:
    op.execute("""
DROP INDEX IF EXISTS idx_item_plastics_plastic_id;
""")
    op.execute("""
DROP TABLE IF EXISTS item_plastics;
""")
