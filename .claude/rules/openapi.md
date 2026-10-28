# API contract rules — baseline

<!-- Bootstrapped by sdlc/plugin/skills/api-forge on the first HTTP run. Edit freely. -->
<!-- These rules are an opinionated default — see "Defaults" in SKILL.md. A team edit here, or an ADR, is the only way to deviate; api-forge reads this file on every run and records deviations in api-sync-report.md. -->

## Where the contract lives

- `docs/features/<slug>/contracts/openapi.yaml` is the source of truth for the HTTP surface. Handlers, clients, mocks and contract tests follow it — never the other way round.
- The contract is **derived** (`data-model.md` + `sad.md` §6 sequences + `PRD.md` AC) by `/sdlc:api-forge <slug>`. After a hand edit or an upstream change, run `/sdlc:api-forge <slug> --reconcile` so `api-sync-report.md` stays true.
- `info.version` bumps only with an explicit CHANGELOG line, never silently.

## Hard rules

- OpenAPI **3.1.0**. Nullability via `type: [string, null]`; `nullable: true` (3.0 style) is forbidden.
- Every error response is the envelope `{code, message, details?}`. `code` is `module.error_name` in snake_case (`lesson.not_found`, `course.not_methodist`) — never free text like `{"error": "failed"}`.
- One error `code` in the contract = one definition in the repo's error registry (constants / enum / sentinel module — whatever the repo uses), returning the **same string** the contract advertises.
- Shared types via `$ref` only; no inline duplicated schemas.
- No `additionalProperties: true` on response shapes. Exception only by ADR (e.g. a polymorphic payload) and noted in the report.
- No real PII in `example` blocks: `<name>@example.test`, `+380 00 000 00 00`, `Test User`.

## Defaults

- URL versioning `/api/v1/...`; never `?v=2` query versioning.
- `BearerAuth` global; a public endpoint declares explicit `security: []`.
- Lists paginate by **cursor** (`?after=&before=&limit=`), wrapped in `{items, has_next, has_prev, next_cursor}`; never offset.
- JSON keys snake_case. Schema names use the domain language of `data-model.md` (`Lesson`, `CreateLessonRequest`) — not a Go/TS/Python idiom, not a driver's error type.
- A mutating endpoint behind a retry or an async actor requires an `Idempotency-Key` header (state the TTL).
- Status by class: `400` validation, `401` no/invalid token, `403` not allowed, `404` existence-hiding, `409` state or uniqueness conflict, `429` rate limit, `5xx` server. Every `4xx`/`5xx` carries the envelope.

## Checks

- `spectral lint docs/features/<slug>/contracts/openapi.yaml` is in the project's check target (`make check` or stack-equivalent).
- A change to the contract and the matching handler/client land in the same PR, with `api-sync-report.md` re-run (`--reconcile`) and its `**Verdict:**` at `PASS` or `PASS (with deferrals)`.

## Repo adaptation — calculate-3d (FastAPI, local-only)

Repo conventions (`CLAUDE.md`, project ADRs) override the baseline defaults above; `api-forge`
records each one as a deviation in `api-sync-report.md`.

- **No auth** (project ADR 0004): no `BearerAuth`; the contract sets global `security: []`. The
  protection boundary is bind `127.0.0.1` + the request guard (feature ADR 0007 of cost-calculator).
- **Paths:** `/api/<module>/...` without `/v1` (`CLAUDE.md` § API shape). One local client that is
  built from the same commit — no versioned consumers.
- **Error envelope:** RFC 9457 `application/problem+json` `{type, title, status, detail, code}` plus
  optional extension members (`errors`, `field`, `items`, `missing`) — already implemented by
  `core/errors.py::problem()`. It plays the role of `{code, message, details?}`: `detail` ≈ `message`,
  extension members ≈ `details`.
- **Error codes:** module errors are `<module>.<error_name>` (`pricing.name_taken`); cross-cutting
  `core` errors are un-namespaced (`validation_error`, `not_found`, `host_not_allowed`,
  `cross_origin_forbidden`, `unsupported_media_type`, `internal_error`). The registry is the set
  of `AppError` subclasses + `core/errors.py`.
- **Status by class:** `422` request validation (FastAPI default, `code: validation_error` with
  `errors[{loc, msg}]`), `409` uniqueness / state conflict, `404` unknown id, `400` disallowed `Host`,
  `403` cross-origin, `415` non-JSON mutating request.
- **Pagination:** a list is paginated by cursor only when a feature ADR does not say otherwise; small,
  fully recomputed lists (cost-calculator ADR 0003) return `{items}` without a cursor.
- **Quantities:** every fractional value is a scaled integer named after its unit
  (`*_kop`, `*_cg`, `*_permille`, `*_s`, `*_w`, `*_h`) — never `number`/float.
- **Generated types:** the running FastAPI app's OpenAPI is what `make api-types` turns into
  `web/src/shared/api/schema.d.ts`. The feature contract is the design-time target; the
  implementation must emit the same paths, schemas and declared error responses.
