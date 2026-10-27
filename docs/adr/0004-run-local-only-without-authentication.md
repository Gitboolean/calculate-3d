---
status: Accepted
owner: "Anton Pohorielov"
reviewers: []
updated_at: "2026-10-27"
feature_size:
stage: "00"
ticket: ""
---

# 0004 — Run the app on localhost only, without authentication (Google OAuth deferred)

- **Status:** Accepted
- **Date:** 2026-10-27
- **Deciders:** Anton Pohorielov (with Claude, `map-architecture` greenfield session)

## Context

The user initially picked Google OAuth (it is baked into base-tpl). The brief, however, defines a
local desktop tool for one user and explicitly excludes multiple users and phone access (§5, §13).
Authentication on a process reachable only from the same machine protects nothing and costs Google
Cloud credentials even in development.

## Decision drivers

- Single user, single machine (brief §3, §5).
- Keep the first working version within ~1 week (brief §10, §12).
- No deployment target (user answer: "local only").

## Considered options

1. **No auth, bind to `127.0.0.1` only** — nothing to configure; the network boundary is the protection.
2. **Google OAuth from day one** — real login flow, needs `GOOGLE_CLIENT_ID/SECRET` and a redirect
   URI even locally.

## Decision outcome

**Chosen:** Option 1. Uvicorn binds to `127.0.0.1` (never `0.0.0.0`); no users/sessions tables; no
deploy pipeline, Docker or monitoring. Google OAuth is **deferred**, not rejected.

## Consequences

**Positive**
- Zero setup: `make run` and open the browser.
- No user/tenant dimension in the data model — simpler schemas and tests.

**Negative**
- Anyone with access to the machine's user session can use and change the data.
- Adding hosting later requires auth + a user dimension (a data-model migration).

**Neutral**
- **Revisit trigger:** any need to reach the app from another device, a deploy to a VPS, or a second
  user → supersede this ADR (Google OAuth is the parked option).

## Links

- `docs/idea-brief.md` §5, §13
- `docs/architecture-map.md` §Constraints
- ADR 0001, ADR 0003
