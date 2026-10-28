---
id: T4
title: "Віддавати index.html для будь-якого не-/api шляху (SPA fallback)"
layer: "wiring"
deps: []
acs: ["AC-09", "AC-14"]
files_hint: ["backend/src/calculate3d/main.py", "backend/tests/integration/test_static_ui.py"]
owner: "Anton Pohorielov"
estimate: "S"
status: "done"
---

# T4 — Віддавати index.html для будь-якого не-/api шляху (SPA fallback)

## Why

[ADR-0001](../adr/0001-route-spa-screens-with-react-router.md): прямі посилання `/catalog/:itemId` і перехід «до налаштувань» (AC-09, AC-14) мають працювати після F5; [sad.md](../sad.md) §7 «Що змінює фіча». Критерії: AC-09, AC-14 у [PRD §5](../PRD.md).

## What

- Замінити `StaticFiles(html=True)` на статику + catch-all, що на будь-який не-`/api` `GET` віддає `web/dist/index.html`; наявні файли (assets) віддаються як є.
- Невідомий `/api/*` і далі повертає problem+json `404 not_found`.

## Definition of Done

- [ ] `GET /settings`, `GET /catalog/0190…` → 200 + вміст `index.html`; `GET /assets/<file>` → сам файл.
- [ ] `GET /api/unknown` → 404 `application/problem+json`, `code: not_found`.
- [ ] `make api-check` зелений.

## Notes

- **Blocked by:** —.
- Спільний `main.py` з T3 → та сама черга (порядок не важливий).
