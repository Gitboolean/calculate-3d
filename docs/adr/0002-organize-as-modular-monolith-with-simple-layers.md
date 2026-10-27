---
status: Accepted
owner: "Anton Pohorielov"
reviewers: []
updated_at: "2026-10-27"
feature_size:
stage: "00"
ticket: ""
---

# 0002 — Organize the backend as a modular monolith with router/service/repo layers, and the web with FSD

- **Status:** Accepted
- **Date:** 2026-10-27
- **Deciders:** Anton Pohorielov (with Claude, `map-architecture` greenfield session)

## Context

The product has a few distinct capability areas (price settings, catalog of items, cost calculation,
later slicer-file import — brief §13) but one user and one process. The code structure is fixed now
because every future feature is slotted into it by `architecture-design` / `implement-tasks`.

## Decision drivers

- One user, one machine (brief §3, §5) — no reason for independently deployed services.
- Keep the cost formula unit-testable without HTTP or DB.
- Learning project: low ceremony, but clear boundaries that the SDLC artifacts can reference.

## Considered options

1. **Modular monolith, simple layers `router → service → repo` per module** — few files, quick start.
2. **Modular monolith, hexagonal `domain / app / infra / api` per module** — strict isolation of
   domain logic; more folders and ports/adapters ceremony.
3. **Microservices** — rejected up-front by the user (not populated, no need at this scale).

## Decision outcome

**Chosen:** Option 1. Each backend module is a vertical slice in
`backend/src/calculate3d/modules/<module>/` (`router.py`, `schemas.py`, `service.py`, `repo.py`,
`tables.py`). Rules that keep the simplicity honest: `service.py` imports neither FastAPI nor
SQLAlchemy (pure business logic, unit-tested); modules talk to each other only via the other
module's `service.py`. The web follows Feature-Sliced Design (`app → pages → widgets → features →
entities → shared`), enforced by Steiger.

## Consequences

**Positive**
- Minimal ceremony; a new feature is one folder modelled on `modules/health/`.
- The cost formula stays pure in `service.py` → fast, deterministic unit tests.

**Negative**
- The domain/infra boundary is a convention, not a structural guarantee — it must be guarded in review
  (`review-feature`) and by the "service has no FastAPI/SQL imports" rule.
- If a module grows complex (e.g. slicer import), it may need a `domain.py`/`importers/` split later.

**Neutral**
- Moving a module to hexagonal later is local to that module (no cross-module rewrite).

## Links

- `docs/architecture-map.md` §Module inventory, §Conventions
- ADR 0001 (stack), ADR 0003 (persistence)
