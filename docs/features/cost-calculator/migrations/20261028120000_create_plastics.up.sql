-- pricing: пластики з поточною ціною за кілограм (US-01, AC-01..03).
-- name — як ввів автор, без пробілів на краях; name_key = casefold(name) рахує застосунок (ADR 0006).
CREATE TABLE IF NOT EXISTS plastics (
    id               TEXT    NOT NULL PRIMARY KEY,
    name             TEXT    NOT NULL,
    name_key         TEXT    NOT NULL,
    price_per_kg_kop INTEGER NOT NULL,
    created_at       TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_plastics_name_key ON plastics (name_key);
