---
status: Accepted
owner: "Anton Pohorielov"
reviewers: []
updated_at: "2026-10-28"
feature_size: M
stage: "04-05"
ticket: ""
---

# 0007 — Guard the local API with a Host allowlist and same-origin checks instead of CSRF tokens

- **Status:** Accepted
- **Date:** 2026-10-28
- **Deciders:** Anton Pohorielov (автор), architecture-design pass

## Context

Інструмент без автентифікації слухає `127.0.0.1` (ADR 0004), і це закриває доступ з інших пристроїв (AC-16). Проте AC-16b вимагає більшого: сторонній сайт, відкритий у браузері **самого автора**, не повинен змінювати чи читати налаштування цін і каталог. Є два вектори. **CSRF** — чужа сторінка шле запит на `http://127.0.0.1:8000/api/...`; браузер його відправить, навіть якщо не дасть прочитати відповідь. **DNS rebinding** — чужий домен після завантаження сторінки переключає свій DNS на `127.0.0.1`. Тоді для браузера запити того ж «origin» і читання відповіді дозволене; сервер помічає лише чужий `Host`. Bind на `127.0.0.1` від жодного з цих векторів не захищає.

## Decision drivers

- QG-3 / AC-16b / PRD §6.1 abuse case «сторонній сайт… зокрема DNS rebinding».
- ADR 0004: без автентифікації, лише локально; захист без стану й облікових записів.
- ADR 0005: правило має діяти однаково для `pricing`, `costing`, `catalog` — тобто в `core`, а не в модулях.
- §2: бюджет одна людина × 2–4 тижні — мінімум рухомих частин у SPA.

## Considered options

1. **Host allowlist + same-origin перевірки** — middleware у `core` для всіх запитів: дозволений лише `Host` з переліку (`127.0.0.1`/`localhost` з портом застосунку та портом Vite); для `/api` — відмова, якщо `Sec-Fetch-Site` дорівнює `cross-site` або `same-site` чи `Origin` присутній і не з переліку; змінні запити приймають лише `Content-Type: application/json`; CORS-дозволів немає.
2. **CSRF-токен (double-submit) + Host allowlist** — не покладається на `Sec-Fetch-*`, але додає cookie, обгортку для `openapi-fetch` і токен у тестах; читання при DNS rebinding однаково зупиняє лише `Host`.
3. **Лише `application/json` + bind** — змушує браузер робити CORS preflight, який без CORS провалюється, тож CSRF зупинено; але після DNS rebinding запит same-origin і preflight не потрібен, тож AC-16b не виконано.

## Decision outcome

**Chosen:** Option 1. Чиста ASGI/Starlette middleware в `core/` (наприклад `core/security.py`), яку `create_app()` реєструє до роутерів:

- **Host:** запит із `Host` поза переліком → problem+json `400` з кодом `host_not_allowed`. Перелік виводиться з налаштувань (`127.0.0.1` і `localhost` × порт застосунку і порт Vite); bind-адреса, як і раніше, не налаштовується.
- **Same-origin для `/api`:** `Sec-Fetch-Site ∈ {cross-site, same-site}` або `Origin` поза переліком → problem+json `403` з кодом `cross_origin_forbidden`. Запити без цих заголовків (curl, TestClient, скрипти на самому комп'ютері) пропускаються: вони вже всередині межі довіри.
- **Content type:** `POST/PUT/PATCH/DELETE` на `/api` з тілом не `application/json` → `415`.
- **CORS:** `CORSMiddleware` не додається ніколи.

Інтеграційні тести покривають кожну відмову і щасливий шлях з `Host` тестового клієнта (тестові налаштування додають `testserver` до переліку).

## Consequences

**Positive**
- Закриває обидва вектори AC-16b, не маючи стану: без токенів, cookie і змін у SPA (браузер сам ставить `Origin`/`Sec-Fetch-Site`).
- Одне місце в `core` — усі нинішні й майбутні модулі захищені автоматично.

**Negative**
- Перелік дозволених адрес треба тримати синхронним із портами `make run`/`make dev`; помилка там ламає розробку (`400` на кожен запит з Vite).
- Захист від CSRF у дуже старих браузерах без `Sec-Fetch-Site` спирається на `Origin` + JSON-only — прийнятно для одного автора з сучасним браузером.

**Neutral**
- Якщо колись перегляд ADR 0004 відкриє доступ з інших пристроїв, ця middleware залишиться, але її доповнить автентифікація.

## Links

- PRD: [[../PRD.md]] AC-16, AC-16b; §6.1
- SAD: [[../sad.md]] §3, §7, §8
- Project ADR: [[../../../adr/0004-run-local-only-without-authentication.md]]
- Related ADR: [[0005-split-feature-into-pricing-costing-catalog-modules]]
