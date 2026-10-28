---
id: T3
title: "Додати middleware захисту запитів: allowlist Host, same-origin, JSON-only"
layer: "wiring"
deps: []
acs: ["AC-16", "AC-16b"]
files_hint: ["backend/src/calculate3d/core/guard.py", "backend/src/calculate3d/core/config.py", "backend/src/calculate3d/main.py", "backend/tests/integration/test_request_guard.py"]
owner: "Anton Pohorielov"
estimate: "M"
status: "todo"
---

# T3 — Додати middleware захисту запитів: allowlist Host, same-origin, JSON-only

## Why

[ADR-0007](../adr/0007-guard-local-api-with-host-allowlist-and-same-origin-checks.md) + [sad.md](../sad.md) §8 «Request guard» і §6 «Cross-cutting: захист локального API»; AC-16 / AC-16b у [PRD](../PRD.md). Коди помилок — [openapi.yaml](../contracts/openapi.yaml) (`HostNotAllowed`, `CrossOriginForbidden`, `UnsupportedMediaType`). Критерії: AC-16, AC-16b у [PRD §5](../PRD.md).

## What

- `core/guard.py`: чиста ASGI/Starlette-middleware. `Host` поза `127.0.0.1`/`localhost` × (порт застосунку, порт Vite) → `400 host_not_allowed`; для `/api` — `Sec-Fetch-Site` `cross-site`/`same-site` або чужий `Origin` → `403 cross_origin_forbidden`; змінний метод без `application/json` → `415 unsupported_media_type`. Відповіді — через `problem()`.
- `core/config.py`: порти для allowlist виводяться з тих самих налаштувань, що й `make run`/`make dev` (sad §11).
- `main.py`: підключити middleware; `CORSMiddleware` не додавати.

## Definition of Done

- [ ] Тести на `400` (чужий `Host`, DNS rebinding), `403` (`Origin: https://evil.example.test`, `Sec-Fetch-Site: cross-site`), `415` (`text/plain` / form POST) — тіло problem+json з правильним `code`.
- [ ] Щасливий шлях: `Host: 127.0.0.1:8000` і `localhost:5173` + same-origin проходять; `GET /api/health` працює.
- [ ] Наявні тести (`TestClient`, `Host: testserver`) лишаються зеленими: фікстура передає дозволений `base_url`, або `testserver` додано в allowlist лише в тестових налаштуваннях.
- [ ] `make api-check` зелений.

## Notes

- **Blocked by:** —.
- Спільний `main.py` з T4/T7/T8/T11 → одна черга. Тест «стан БД незмінний після відмови» на реальних ендпоінтах — у T12, бо зараз змінних ендпоінтів ще немає. Bind `127.0.0.1` уже покрито `tests/unit/test_run.py`.
