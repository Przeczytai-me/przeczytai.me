# Authentication in PrzeczytAI

## How it works

Authentication is handled entirely by [Clerk](https://clerk.com). Clerk sits in front of every request as a proxy layer — before any page or API route runs, Clerk intercepts the request, validates the session, and attaches the user's identity to it.

### Request lifecycle

1. User visits any route
2. `src/proxy.ts` runs (Next.js 16's equivalent of `middleware.ts`) — Clerk validates the session cookie
3. If the route is protected and there is no valid session → Clerk redirects to `/sign-in`
4. If the session is valid → request proceeds to the page/route handler
5. Inside server components, `auth()` returns `userId` and other session data decoded from the JWT — no network call required

### Session storage

Clerk stores the session in a **cookie** (HttpOnly, Secure). The browser sends it automatically on every request. The cookie contains a signed JWT — Clerk validates it cryptographically without hitting a database on each request.

### Sign-in / sign-up flow

Clerk hosts the sign-in and sign-up UI. The pages at `/sign-in` and `/sign-up` simply render Clerk's `<SignIn />` and `<SignUp />` components. Clerk handles:

- Email/password authentication
- OAuth providers (Google, GitHub, etc.) — configured in the Clerk dashboard
- Email verification, password reset, MFA — all out of the box

After successful authentication, Clerk sets the session cookie and redirects the user back to the app.

---

## Why a database is not needed for basic auth

User identity lives in Clerk's infrastructure, not in your own database. Everything you need for auth is available without any database lookup:

| Data | Where it lives | How to access |
|---|---|---|
| User ID | JWT (cookie) | `auth()` on the server, `useAuth()` on the client |
| Email, name, avatar | Clerk's database | `currentUser()` on the server, `useUser()` on the client |
| Session state | Clerk's servers | Validated automatically by the proxy |

A database becomes necessary only when you have **your own data tied to users** — e.g. posts, bookmarks, orders. In that case the pattern is: store Clerk's `userId` as a foreign key in your tables, and sync user creation/deletion via a Clerk webhook. The user profile itself still lives in Clerk.

---

## Decisions made in this project

### `proxy.ts` for route protection (not per-page guards)

Next.js 16 replaced `middleware.ts` with `proxy.ts`. The proxy runs on the **edge**, before any page renders, which means:

- Protected pages are never even executed for unauthenticated users — no accidental data leaks from server components
- One central place to define what is public vs. protected — easier to audit and maintain
- No need to add an `auth()` guard at the top of every protected page

The trade-off: it's coarser-grained. When you need per-page logic (e.g. redirect to a specific URL, or check a role), use `auth()` inside the server component in addition to the proxy.

Protected routes are defined as:

```ts
const isProtectedRoute = createRouteMatcher([
  "/app(.*)",
  "/api(.*)",
  "/trpc(.*)",
]);
```

Only those route groups are blocked automatically. Unknown page URLs fall through to the app-level not-found handler, which redirects back to `/`.

### `auth()` inside server components (not client-side hooks)

Where user data is needed server-side (e.g. `/app`), `auth()` and `currentUser()` are called directly in the async server component. This means:

- No client/server waterfall — user data is fetched during the server render
- No loading states needed for auth-gated content
- The `userId` is available synchronously from the JWT, `currentUser()` makes one Clerk API call when full profile data is needed

### Custom `SignOutButton` client component

Clerk's `<SignOutButton>` from `@clerk/nextjs` requires exactly one child element, which creates awkward wrapper JSX. Instead, a minimal client component (`src/components/sign-out-button.tsx`) calls `useClerk().signOut()` directly. This is a plain button with a `className` prop — no wrapper pattern, fully styleable.

### `ClerkProvider` at the root layout

`ClerkProvider` wraps the entire app in `src/app/layout.tsx`. This gives every client component in the tree access to Clerk's React context (hooks like `useUser`, `useAuth`). It has no effect on server components — those use `auth()` / `currentUser()` from `@clerk/nextjs/server` directly.
