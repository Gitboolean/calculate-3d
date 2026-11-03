-- catalog: вироби — лише параметри, ніколи не ціна (US-04..06, ADR 0003).
-- name / name_key — як у plastics (ADR 0006).
CREATE TABLE IF NOT EXISTS items (
    id           TEXT    NOT NULL PRIMARY KEY,
    name         TEXT    NOT NULL,
    name_key     TEXT    NOT NULL,
    print_time_s INTEGER NOT NULL,
    created_at   TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_items_name_key ON items (name_key);
