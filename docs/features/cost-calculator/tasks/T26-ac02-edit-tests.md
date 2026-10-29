---
id: T26
title: "Покрити шлях редагування пластику з AC-02 integration- і UI-тестами"
layer: "tests"
deps: ["T24"]
acs: ["AC-02"]
files_hint: ["backend/tests/integration/test_pricing_api.py", "web/src/pages/settings/ui/PlasticsSection.test.tsx"]
owner: "Anton Pohorielov"
estimate: "S"
status: "todo"
---

# T26 — Покрити шлях редагування пластику з AC-02 integration- і UI-тестами

## Why

Follow-up з рев'ю [review-2026-10-29](../_review/review-2026-10-29.md). Критерії: AC-02 у [PRD §5](../PRD.md).

## Definition of Done

- [ ] Integration: PUT /api/pricing/plastics/{id} на зайняту назву → 409 pricing.name_taken, ціна 0 → 422; GET після цього повертає старі значення. Vitest: PlasticsSection — форма «Змінити» з невалідною ціною показує помилку біля поля і не шле PUT; make check зелений. Знахідка S1-10 у docs/features/cost-calculator/_review/review-2026-10-29.md.

## Notes

- **Blocked by:** T24.
