# Frontend Supabase Auth Implementation Specification (Codex)

## Objective
Implement first-class Supabase authentication in the React/Vite frontend so every protected API call and SSE stream is tied to a validated Supabase user, aligns with the backend auth/metering spec, and fits the existing design system without introducing Supabase-provided UI chrome.

## Scope
- Add Supabase email/password auth with optional magic link and OAuth (Google, GitHub).
- Persist session, refresh tokens, and keep `access_token` available for API/SSE.
- Gate resume generation and history features behind authentication.
- Surface usage/limit responses (`402 LIMIT_REACHED`) and drive users to billing entrypoints.
- Fit into the current frontend architecture (single-page flow with `ApiClient`, `useProcessingJob`, and existing design system).

## Non-Goals
- Building a full account settings area (profile editing, billing management UI).
- Implementing backend endpoints or database schema (covered by backend spec).
- Replacing the design system with Supabase UI components.

## Dependencies and Config
- Add `@supabase/supabase-js@^2` to `frontend/package.json`.
- Environment (add to `.env.example` and `.env.production` as needed):
  - `VITE_SUPABASE_URL=<project-url>`
  - `VITE_SUPABASE_ANON_KEY=<anon-key>`
  - `VITE_SUPABASE_REDIRECT_URL=<https://app.example.com/auth/callback>` (used for magic link/password reset).
  - Optional flags:
    - `VITE_SUPABASE_AUTH_PROVIDERS=google,github`
    - `VITE_SUPABASE_AUTH_FLOW=magic_link|password` (default: password).

## Architecture and Data Flow
- **Supabase client** (`frontend/src/lib/supabaseClient.ts`):
  - Create a singleton with `createClient(url, anonKey, { auth: { persistSession: true, storageKey: 'resumeoptimizer.supabase.auth' } })`.
  - Export helpers to fetch the latest session/access token.
- **Auth state container** (`frontend/src/hooks/useSupabaseAuth.ts` + `AuthProvider` in `frontend/src/components/auth/AuthProvider.tsx`):
  - Holds `{ user, session, status: 'idle'|'loading'|'authenticated'|'unauthenticated', error }`.
  - Subscribes to `supabase.auth.onAuthStateChange` to react to sign-in/out and token refresh.
  - Exposes actions: `signInWithPassword`, `signUpWithPassword`, `sendMagicLink`, `signInWithOAuth(provider)`, `signOut`, `resetPassword`.
- **Token bridge for API client**:
  - Extend `ApiClient` to accept an async token provider (e.g., `auth.getAccessToken()`).
  - For every request, if a token exists, set `Authorization: Bearer <access_token>`.
  - For SSE (`useProcessingJob`), append `?access_token=<token>` to the stream URL (EventSource cannot set headers) and include the token on snapshot GETs.
- **Protected interaction points**:
  - `InputScreen` and any CTA that triggers `/api/pipeline/start` must require `status === 'authenticated'`; otherwise prompt auth modal.
  - History/list endpoints and export/download URLs must include the token.
- **Error handling**:
  - Centralize handling for `401/403` to force sign-out and show re-auth prompt.
  - Map `402 LIMIT_REACHED` to UI paywall (reuse/extend existing billing entrypoint).

## UX and Interaction Requirements
- **Entry points**: Top-right auth menu (Sign in/Sign up when logged out; avatar/initials + dropdown when logged in) available on all screens.
- **Auth modal/drawer**:
  - Tabs for Sign in / Sign up; mode switches without losing typed input.
  - Supports password flow; optional magic-link CTA; OAuth buttons if enabled via env.
  - Copy uses product voice; no Supabase branding.
  - Validation: email format, password min length 8; inline error display from Supabase errors.
- **Session awareness**:
  - On load, show a lightweight loading state while restoring session; avoid flashing logged-out UI.
  - If a token expires mid-session, auto-refresh via Supabase; on refresh failure, show a toast and prompt to re-authenticate.
- **Gating generation**:
  - If unauthenticated and user clicks "Start", open auth modal; on success, resume action automatically.
  - Display signed-in email and remaining usage if backend returns it.
- **Billing/limits surfacing**:
  - When API returns `402 LIMIT_REACHED`, show a blocking banner or modal with CTA to billing/checkout endpoint.

## API and Networking Requirements
- **Header contract**: All protected requests must include `Authorization: Bearer <access_token>`.
- **SSE**: Use `EventSource(<streamUrl>?access_token=token)`; ensure token is URL-encoded and refreshed if the job is long-running (recreate EventSource on token change).
- **File uploads**: Include `Authorization` and `X-Client-Id` on multipart uploads as well.
- **Retries**: For transient network errors, retry idempotent GETs once; do not auto-retry auth errors.

## Security and Privacy
- Never store the Supabase service key in the frontend; only the anon key is used.
- Keep auth state in memory + Supabase-managed storage; do not duplicate tokens in `localStorage` manually.
- Sanitize all Supabase error messages shown to users.
- Use `sameSite=lax` cookies only if Supabase Hosted Auth domain matches; otherwise rely on local storage (default in supabase-js v2).

## Component/Hook Contract Changes
- `ApiClient`:
  - Accept constructor option `getAccessToken?: () => Promise<string | null>`.
  - `request`/`upload`/`export` methods call the provider and attach `Authorization` when present.
- `useProcessingJob`:
  - Accept `accessToken?: string` and inject it into stream URL; reconnect when token changes.
- `InputScreen`/`ProcessingScreen`/`RevealScreen`:
  - Receive auth context via `AuthProvider` wrapping `App`.
  - Disable primary actions while `auth.status === 'loading'`.
- New UI elements:
  - `AuthModal`, `AuthMenu`, `ProtectedAction` (wrapper to gate a button/handler until signed in).

## Edge Cases
- Token refresh during an active SSE stream: when `access_token` changes, close and reopen EventSource with the new token.
- Magic link flow: on redirect back to the app, read `code`/`type` params and call `supabase.auth.exchangeCodeForSession`; show success/failure toast.
- Password reset: handle `type=recovery` by showing "set new password" screen that calls `updateUser`.
- Multi-tab: Supabase client emits auth changes across tabs; ensure `AuthProvider` updates state accordingly.

## Testing Plan
- Unit: auth hook actions (sign in/out, error states), token injection in `ApiClient`.
- Integration: start pipeline when logged out triggers auth modal; after login, request proceeds with `Authorization`.
- SSE: verify stream connects with token, reconnects on token change, and fails gracefully on 401.
- Browser: Chrome/Firefox/Safari/Edge latest; mobile Safari/Chrome for modal and session restoration.

## Acceptance Criteria
- Users can sign up, sign in, sign out, and recover via magic link/password reset (when enabled) without leaving the SPA.
- All protected API calls include Supabase access tokens; unauthenticated calls are blocked and redirected to auth.
- SSE streaming for processing jobs works while authenticated and recovers on token refresh.
- UI clearly indicates signed-in state and handles `402 LIMIT_REACHED` with a paywall prompt.
- No Supabase-branded UI appears; design matches existing styling and typography.

## Implementation Checklist
1. Add supabase-js dependency and env vars.
2. Create `supabaseClient` and `AuthProvider`/`useSupabaseAuth`.
3. Extend `ApiClient` and `useProcessingJob` to consume access tokens.
4. Implement auth modal/menu and gate generation/history actions.
5. Wire magic link/password reset callback handling.
6. QA per testing plan; document env setup in `frontend/README` or `.env.example`.
