---
status: Accepted
owner: "Anton Pohorielov"
reviewers: []
updated_at: "2026-11-09"
feature_size: M
stage: "04-05"
ticket: ""
---

# 0005 — Add an importing module that owns the parser and the filament mappings

- **Status:** Accepted
- **Date:** 2026-11-09
- **Deciders:** Anton Pohorielov (автор), architecture-design pass

## Context

Фіча додає дві речі, яких у бекенді немає: розбір файлу слайсера (ADR 0001) і збережені зіставлення пластиків (ADR 0003). У репо модуль — вертикальний зріз `router · schemas · service · repo · tables`; модулі звертаються один до одного лише через `service.py`, а чужі `repo`/`tables` імпортувати заборонено (`tests/unit/test_module_boundaries.py`). Отже, власник таблиці зіставлень визначає напрям залежностей, префікс API (а з ним і згенеровані типи вебу) та міграцію. Пізніше перенесення таблиці між модулями означає нову міграцію, переписані виклики й типи (≥ 3 днів).

## Decision drivers

- project ADR 0002: модульний моноліт, модулі — через `service.py`.
- cost-calculator ADR 0005: модулі `pricing` / `costing` / `catalog` з ланцюжком залежностей `catalog → costing → pricing`.
- CONTEXT: зіставлення пластиків — NOT пластик, власної ціни не має; змінюється лише під час імпорту (PRD §3).
- §2: бюджет E = 2 тижні; мінімум змін у вже змердженому етапі 1.

## Considered options

1. **Новий модуль `importing`** — парсер і таблиця зіставлень в одному модулі `modules/importing/`, маршрут `/api/importing`, коди помилок `importing.*`.
2. **Зіставлення в `pricing`** — парсер у новому `importing`, а таблиця зіставлень у `pricing` поряд із пластиками («псевдоніми слайсера» пластику).

## Decision outcome

**Chosen:** Option 1. Увесь імпорт — розбір, підстановка й запам'ятовування зіставлень — живе в одному модулі, а `pricing` і `costing` лишаються без змін. Зіставлення за глосарієм не є частиною налаштувань цін: ціни воно не має і редагується лише під час імпорту.

- Залежності сервісів: `catalog → importing` (запам'ятати зіставлення, ADR 0003) і `importing → pricing` (чи є пластики й налаштування цін — AC-04). Наявні `catalog → costing → pricing` лишаються. `importing` нічого не знає про `catalog`.
- Таблиця зіставлень посилається на `plastics(id)` через FK з `ON DELETE CASCADE` — FK через межу модуля, з прецедентом `item_plastics` (catalog → pricing). Це зв'язок рівня схеми, а не імпорт коду.
- Розбір — окремий `parser.py` (чиста функція без I/O, як `costing/domain.py`), тож юніт-тести парсера не торкаються БД.

## Consequences

**Positive**
- Імпорт ізольований: його можна розширити (OrcaSlicer) або прибрати, не чіпаючи налаштувань цін.
- `pricing` не росте й не дізнається про слайсер; видалення пластику забуває зіставлення каскадом.

**Negative**
- Ще один FK через межу модуля (`importing` → `plastics`), який тест меж модулів не бачить — його покриває міграційний та інтеграційний тест AC-11.
- `catalog` отримує нову залежність від `importing` (ADR 0003).

**Neutral**
- Назву `importing` обрано в ряду `pricing` / `costing`; `import` — зарезервоване слово Python.

## Links

- PRD: [[../PRD.md]] US-01..US-05; AC-04, AC-07, AC-11; §3
- SAD: [[../sad.md]] §5
- Related ADR: [[0001-parse-slicer-file-on-server-and-keep-only-numbers]], [[0003-remember-filament-mappings-in-the-item-save-transaction]]
- cost-calculator ADR: [[../../cost-calculator/adr/0005-split-feature-into-pricing-costing-catalog-modules.md]]
- Project ADR: [[../../../adr/0002-organize-as-modular-monolith-with-simple-layers.md]]
