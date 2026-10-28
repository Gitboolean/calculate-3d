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

CREATE INDEX IF NOT EXISTS idx_item_plastics_plastic_id ON item_plastics (plastic_id);
