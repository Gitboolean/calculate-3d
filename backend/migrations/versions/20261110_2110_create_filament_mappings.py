"""create filament mappings

Promoted verbatim from
docs/features/print-file-import/migrations/20261110120000_create_filament_mappings.{up,down}.sql.

Revision ID: f6268165ee91
Revises: 65f15a51514f
Create Date: 2026-11-10 21:10:00
"""

from alembic import op

revision: str = "f6268165ee91"
down_revision: str | None = "65f15a51514f"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.execute("""
-- importing: зіставлення пластиків — запам'ятаний вибір «філамент слайсера (назва + колір) → пластик»
-- (US-03, AC-07..AC-11; ADR 0003, ADR 0005). Пишеться лише в транзакції збереження виробу.
-- filament_name — назва пресету з файлу, лише без пробілів на краях, з урахуванням регістру (AC-09);
-- filament_color — '#RRGGBB' у верхньому регістрі, альфу відкинуто (SAD §8). Нормалізує застосунок,
-- тож бінарне порівняння SQLite (BINARY collation) і є правилом збігу AC-09.
-- Видалення пластику каскадно забуває його зіставлення (AC-11): pricing про них не знає.
CREATE TABLE IF NOT EXISTS filament_mappings (
    id             TEXT NOT NULL PRIMARY KEY,
    filament_name  TEXT NOT NULL,
    filament_color TEXT NOT NULL,
    plastic_id     TEXT NOT NULL REFERENCES plastics (id) ON DELETE CASCADE,
    created_at     TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);
""")
    op.execute("""
CREATE UNIQUE INDEX IF NOT EXISTS uq_filament_mappings_name_color
    ON filament_mappings (filament_name, filament_color);
""")
    op.execute("""
CREATE INDEX IF NOT EXISTS idx_filament_mappings_plastic_id ON filament_mappings (plastic_id);
""")


def downgrade() -> None:
    op.execute("""
DROP INDEX IF EXISTS idx_filament_mappings_plastic_id;
""")
    op.execute("""
DROP INDEX IF EXISTS uq_filament_mappings_name_color;
""")
    op.execute("""
DROP TABLE IF EXISTS filament_mappings;
""")
