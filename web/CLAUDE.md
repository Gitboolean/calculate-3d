# web/ — notes for agents

Root conventions: `../CLAUDE.md`. Node 24+, npm.

- FSD layers import only downward: app → pages → widgets → features → entities → shared. Import
  another slice only through its `index.ts`; inside a slice use relative imports. Alias `@/` = `src/`.
- Precedent for a new screen: `src/pages/home/` (Card) + `src/entities/health/` (TanStack Query hook
  over the typed `api` client from `@/shared/api`). Copy that shape.
- shadcn/ui: add primitives with `npx shadcn add <component>` (lands in `src/shared/ui/`, re-export it
  from `src/shared/ui/index.ts`); never hand-roll an equivalent or add a second styling system.
- API types: `src/shared/api/schema.d.ts` is generated (`make api-types`) — do not edit by hand.
- Tests: `*.test.tsx` next to the component; stub `globalThis.fetch` (the client resolves fetch per
  call) and wrap in a fresh `QueryClient` with `retry: false`.
- Steiger exemptions live in `steiger.config.ts` with a reason each — keep them narrow.
- TypeScript is pinned to 5.9: `openapi-typescript` and `typescript-eslint` don't accept 6+/7 yet.
