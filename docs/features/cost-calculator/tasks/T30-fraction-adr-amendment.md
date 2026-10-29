---
id: T30
title: "Задокументувати точні Fraction-проміжні обчислення в ADR 0004 і CLAUDE.md"
layer: "docs"
deps: []
acs: ["AC-08", "AC-08b"]
files_hint: ["docs/features/cost-calculator/adr", "CLAUDE.md", "backend/CLAUDE.md", "docs/features/cost-calculator/sad.md"]
owner: "Anton Pohorielov"
estimate: "S"
status: "todo"
---

# T30 — Задокументувати точні Fraction-проміжні обчислення в ADR 0004 і CLAUDE.md

## Why

Follow-up з рев'ю [review-2026-10-29](../_review/review-2026-10-29.md). Критерії: AC-08, AC-08b у [PRD §5](../PRD.md).

## Definition of Done

- [ ] ADR 0004 (поправка з датою), ADR 0005 і CLAUDE.md § Money кажуть: проміжні суми — точні fractions.Fraction, округлення до копійок через Decimal-контекст (ROUND_CEILING для донату, ROUND_HALF_UP для рядків); sad.md і T5 не суперечать; make check зелений. Знахідка S1-7 у docs/features/cost-calculator/_review/review-2026-10-29.md.

## Notes

- **Blocked by:** —.
