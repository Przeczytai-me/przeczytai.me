# Frontend Agent Instructions

This folder contains the PrzeczytAI.me frontend application.

## Stack

- Next.js 16 App Router with React 19 and TypeScript.
- Tailwind CSS 4 for styling.
- shadcn/ui with the `base-nova` style and `lucide-react` icons.
- Base UI where lower-level accessible primitives are needed.
- Clerk for authentication.
- TanStack Query for client-side server state.
- Biome for linting and formatting.
- Local dictionary-based internationalization in `src/i18n/`; Polish is the
  default locale.

## Next.js

This is not the older Next.js API surface. Before writing or changing Next.js
code, read the relevant guide in `node_modules/next/dist/docs/` and follow the
current conventions. Pay particular attention to App Router, Route Handlers,
server/client component boundaries, proxy/middleware conventions, and
deprecations.

## UI And Components

- Build new reusable UI from shadcn/ui components when a matching component
  exists.
- Use `lucide-react` icons for icon buttons and visual actions.
- Keep user-facing text in the dictionary files under `src/i18n/` instead of
  hard-coding strings in components.
- Keep components focused and action-specific. Avoid growing a single
  dashboard or page component into an all-purpose file.
- Follow existing aliases from `components.json`, especially `@/components`,
  `@/components/ui`, `@/lib`, and `@/lib/utils`.

## Auth And API

- Browser-facing frontend calls use same-origin `/api/v1/*` paths.
- Route Handlers proxy backend calls through `src/lib/backend-fetch.ts`.
- Protected backend calls must use a Clerk bearer token from the
  `przeczytai-api` JWT template.
- Do not send `x-api-key` or `userId` from the frontend.
- Keep `/app` as the post-auth destination after successful sign-in or sign-up.

## Commands

Run commands from this `frontend/` directory:

```bash
pnpm dev
pnpm lint
pnpm lint:fix
pnpm format
pnpm build
```

Use `pnpm lint` before handing off frontend edits. Use `pnpm build` for changes
that affect routing, server code, authentication, or framework configuration.
