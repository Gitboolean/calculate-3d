-- pricing: налаштування цін — рівно один рядок (AC-04, AC-05, AC-09).
-- Рядка немає = «не задано». Застосунок завжди пише фіксований id (константа в pricing,
-- 00000000-0000-7000-8000-000000000001) через INSERT … ON CONFLICT (id) DO UPDATE усіх полів —
-- тож другий рядок неможливий, а очистити поля назад неможливо за побудовою. Не seed: до першого
-- збереження рядка бути не повинно.
CREATE TABLE IF NOT EXISTS price_settings (
    id                  TEXT    NOT NULL PRIMARY KEY,
    tariff_per_kwh_kop  INTEGER NOT NULL,
    printer_power_w     INTEGER NOT NULL,
    printer_price_kop   INTEGER NOT NULL,
    printer_lifetime_h  INTEGER NOT NULL,
    parts_per_hour_kop  INTEGER NOT NULL,
    scrap_rate_permille INTEGER NOT NULL,
    created_at          TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);
