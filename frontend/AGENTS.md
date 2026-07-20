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
- Fumadocs for the `/docs` experience, with MDX content under `content/docs/`.
- MSW for opt-in, development-only frontend API mocks.
- Local dictionary-based internationalization in `src/i18n/`; Polish is the
  default locale.

## Next.js

This is not the older Next.js API surface. Before writing or changing Next.js
code, read the relevant guide in `node_modules/next/dist/docs/` and follow the
current conventions. Pay particular attention to App Router, Route Handlers,
server/client component boundaries, proxy/middleware conventions, and
deprecations.

- Use Server Components by default. Add `"use client"` only when browser APIs,
  state, effects, or interactive event handlers require it.
- Keep client boundaries as small as practical instead of turning an entire
  page into a Client Component.
- Keep `page.tsx` and `layout.tsx` focused on routing, data boundaries,
  metadata, and composing the page. Move reusable rendering and interaction
  logic into adjacent components.
- Use default exports where Next.js requires them. Prefer named exports for
  reusable components and hooks.

## UI And Components

- Build new reusable UI from shadcn/ui components when a matching component
  exists.
- Use `lucide-react` icons for icon buttons and visual actions.
- Keep application UI text in the dictionary files under `src/i18n/` instead
  of hard-coding strings in components. Keep documentation prose in the MDX
  files under `content/docs/`.
- Follow existing aliases from `components.json`, especially `@/components`,
  `@/components/ui`, `@/lib`, and `@/lib/utils`.

## Component And Hook Structure

- Move substantial page JSX into meaningful, focused components such as forms,
  cards, tables, lists, badges, toolbars, and page sections.
- Split components by responsibility, not by an arbitrary file-length limit.
  Do not extract trivial one-off markup.
- Place route-specific components in the route's `_components/` directory. Put
  components reused across routes under `src/components/`.
- Keep generic design-system primitives under `src/components/ui/`. Do not put
  product-specific behavior into these primitives.
- Give components domain-specific names that explain their purpose, such as
  `ReadingStatusBadge` rather than `StatusComponent`.
- Extract reusable or sufficiently complex stateful logic into custom hooks.
- Keep shared hooks under `src/hooks/`; place route-specific hooks close to
  their consumers.
- Do not create a custom hook for trivial, single-use logic solely to reduce
  component length.
- Keep state as local as possible. Lift it only when multiple components need
  to coordinate.
- Derive values from existing state or props instead of storing duplicate
  state.
- Do not use `useEffect` for derived values or normal event handling. Use it
  only to synchronize with external systems.
- Custom hooks should expose a small, intentional API rather than returning all
  internal state and setters.

## Auth And API

- Browser-facing frontend calls use same-origin `/api/v1/*` paths.
- Route Handlers for implemented backend contracts proxy calls through
  `src/lib/backend-fetch.ts`.
- Protected backend calls must use a Clerk bearer token from the
  `przeczytai-api` JWT template.
- Do not send `x-api-key` or `userId` from the frontend.
- Development-only MSW mocks are enabled with
  `NEXT_PUBLIC_API_MOCKING=true`. Keep existing live `/api/v1/*` routes live,
  mock only missing contracts, and allow unmatched requests to pass through.
- Keep `/app` as the post-auth destination after successful sign-in or sign-up.

## Data And API Logic

- Use TanStack Query for client-side server state. Do not fetch server data
  manually through `useEffect`.
- Keep request construction, response parsing, and API types outside UI
  components, preferably in `src/lib/api.ts` or focused API modules.
- Put query and mutation configuration in reusable hooks when multiple
  components use the same operation.
- Handle loading, empty, error, and success states explicitly for data-driven
  UI.
- Do not copy server data into local state unless the user is editing a
  temporary draft.

## Types And Maintainability

- Avoid `any`. Validate or narrow unknown external data at its boundary.
- Move reusable constants, types, validation rules, and pure transformations
  out of component files.
- Keep product logic out of presentational components where separating it
  makes the component easier to test.
- Avoid premature shared abstractions. Extract something into shared code only
  when it has multiple real consumers or a stable reusable responsibility.

## Accessibility And Behavior

- Use semantic HTML before adding ARIA attributes or custom interaction
  behavior.
- Every interactive control must have an accessible name and visible keyboard
  focus.
- Preserve keyboard behavior when wrapping or extending shadcn/Base UI
  components.
- Keep destructive actions explicit and require confirmation when accidental
  activation could cause data loss.

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
Browser-check interactive frontend changes at relevant desktop and mobile
viewport sizes.
