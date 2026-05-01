# Resume Optimizer - Frontend v2

A conversational, "single chat surface" rewrite of the Resume Optimizer UI.
Instead of tabs and multi-step forms, the entire app (`Auth -> Input -> Processing
-> Reveal`) is expressed as one evolving conversation: typography-first, airy
gradient background, and UI modules (pills, drop zones, auth options) that
materialize only when the agent asks for them.

> **Status:** Phases 1-5 are implemented:
>
> - **Phase 1** - shell + global `ConversationState`
> - **Phase 2** - contextual choices + file upload
> - **Phase 3** - auth gate wired to Supabase (with a dev-bypass)
> - **Phase 4** - live SSE processing stage (with a scripted mock for
>   offline dev)
> - **Phase 5** - the resume/review flow is wired end-to-end: `ResumeStage`
>   and `ReviewActions` render the canonical review payload, `AppShell`
>   switches into the `REVIEWING` two-column layout, the backend persists
>   review documents, and the frontend can load them through
>   `GET /api/applications/{id}/review`.

## Quick start

```bash
cd frontend_v2
npm install
npm run dev
```

Dev server runs on **http://localhost:3001** so it does not collide with the
legacy frontend (`:3000`).

Copy `.env.example` -> `.env.local` and set the relevant vars:

- `VITE_API_URL` - FastAPI base URL (default `http://localhost:8000`)
- `VITE_SUPABASE_URL` / `VITE_SUPABASE_PUBLISHABLE_KEY` - real Supabase auth
- `VITE_AUTH_BYPASS=true` - skip Supabase, use a fake signed-in user
- `VITE_MOCK_STREAM=true` - replay a scripted SSE timeline in-browser

**Zero-setup demo:** leave all Supabase vars empty and set both
`VITE_AUTH_BYPASS=true` and `VITE_MOCK_STREAM=true`. Missing Supabase
credentials alone do **not** enable auth bypass, so the bypass flag is
required to click through the full
`gather -> auth -> processing -> reviewing` flow with no backend running.

## Architecture at a glance

```text
src/
|-- App.tsx                      # Mounts <AppShell/>
|-- main.tsx                     # ReactDOM entry
|-- index.css                    # Tailwind v4 + @theme tokens + utilities
|-- lib/
|   |-- cn.ts                    # clsx + tailwind-merge
|   |-- supabase.ts              # Lazy Supabase client (null when unconfigured)
|   `-- api.ts                   # startPipeline / uploadResume + review fetches
|-- types/
|   `-- streaming.ts             # SSE event shapes + STEP_LABELS
|-- auth/
|   |-- AuthContext.tsx          # Supabase session + dev-bypass
|   `-- AuthGateBridge.tsx       # Auto-advances out of AUTH_GATE on sign-in
|-- shell/
|   |-- AppShell.tsx             # Gradient canvas, header, context strip, feed
|   |-- ProfileMenu.tsx          # Top-right glass profile chip
|   |-- GeminiStar.tsx           # Top-center brand sparkle glyph
|   `-- ResumeStage.tsx          # Review-mode resume paper stage
`-- conversation/
    |-- types.ts                 # Phase, Message, AgentUI, CollectedData
    |-- script.ts                # Ordered ScriptStep[] (the "brain")
    |-- ConversationContext.tsx  # Reducer + provider + useConversation()
    |-- ConversationFeed.tsx     # Active-turn stage
    |-- ContextStrip.tsx         # Chips derived from state.data
    |-- MessageBubble.tsx        # Agent hero prose + user pills
    |-- ChoicePills.tsx          # Floating option pills
    |-- FileDropZone.tsx         # Drop zone + inline AttachedFilePill
    |-- AuthPills.tsx            # Google OAuth pill, wired to AuthContext
    |-- Composer.tsx             # Pill input + contextual UI slot
    |-- ProcessingStream.tsx     # Live processing stage + review handoff
    |-- ReviewActions.tsx        # Download/copy actions for the review payload
    |-- useProcessingJob.ts      # SSE subscription (real + scripted mock)
    `-- useTypewriter.ts         # Per-character hero reveal
```

### Global state machine

```text
IDLE -> GATHERING_INFO -> AUTH_GATE -> PROCESSING -> REVIEWING
```

Each `ScriptStep` declares the phase it transitions into, the agent's prompt,
and the `AgentUI` module to expose (text / choices / file / auth). The reducer
in `ConversationContext.tsx` advances the cursor based on the step's
`handle(...)` response.

### Contextual UI contract

Any `AgentMessage` can carry a `ui` descriptor:

```ts
ui: { kind: 'choices', choices: [{ value: 'mid', label: 'Mid-level' }] }
ui: { kind: 'file',    accept: '.pdf,.docx', allowText: true }
ui: { kind: 'text',    placeholder: 'Paste the JD...', multiline: true }
ui: { kind: 'auth',    providers: ['google', 'email'] }
ui: { kind: 'none' }
```

The `Composer` reads that descriptor and renders the matching floating module
above the pill input. Modules enter/leave via `AnimatePresence`; nothing
snaps.

## Adding a new step

1. Append a `ScriptStep` to `src/conversation/script.ts`.
2. Return the new step's `id` from the previous step's `handle(...)`.
3. (Optional) Set `phase` to drive layout changes in `AppShell`.

That is it; no routing or component wiring needed.

## Styling notes

- Tailwind v4 CSS-first config lives entirely in `src/index.css` via
  `@theme`; there is no `tailwind.config.js`.
- Design tokens: `ink-{50..900}` (neutrals), `sky-{50..500}` (soft sky
  accents), `star-{blue,red,yellow,green}` (Gemini glyph hues), plus utility
  classes `.shell-gradient` (center-bottom radial bloom), `.glass`,
  `.glass-sky`, `.soft-shadow(-lg)`, `.orb-pulse`, `.fade-to-muted`.
- Elevation is expressed via soft shadows, not borders.
