# PrzeczytAI.me Agent Instructions

This repository contains the PrzeczytAI.me product: a Polish text-to-speech web
app with a Next.js frontend, Python backend, infrastructure code, and product
documentation.

## Repository Layout

- `frontend/` contains the customer-facing Next.js application.
- `backend/` contains the Python API implementation and tests.
- `infrastructure/` contains deployment and cloud infrastructure code.
- `docs/` contains architecture notes and integration contracts.
- `tests/` contains repository-level integration tests.

## General Rules

- Prefer the closest scoped `AGENTS.md` when one exists.
- Keep backend and frontend changes isolated unless the task explicitly spans
  both systems.
- Treat `docs/frontend-clerk-api-integration.md` as the source of truth for
  frontend/backend auth integration.
- Preserve the public frontend API surface as `/api/v1/*`.
- Successful sign-in or sign-up should land users on `/app`.
- Use existing project conventions before introducing new tools or patterns.

## Git Workflow

- Use Conventional Commits structure for commit messages.
- Pull request titles must follow
  `<type>(<LINEAR_TICKET_OR_SERVICE>): <description>`. Use the Linear ticket
  number when one exists and the service name otherwise. Examples:
  - `feat(PRZ-44): add authenticated application shell`
  - `fix(PRZ-56): enable API mocking in development`
  - `chore(frontend): update dependencies`
  - `ci(infrastructure): add deployment validation`
- Pull requests may be based from a `codex/...` branch, but the PR title should
  not include `codex`.
