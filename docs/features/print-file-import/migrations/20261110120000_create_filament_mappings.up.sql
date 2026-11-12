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

CREATE UNIQUE INDEX IF NOT EXISTS uq_filament_mappings_name_color
    ON filament_mappings (filament_name, filament_color);

CREATE INDEX IF NOT EXISTS idx_filament_mappings_plastic_id ON filament_mappings (plastic_id);
