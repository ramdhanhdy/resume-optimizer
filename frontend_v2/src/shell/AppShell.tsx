import { AnimatePresence, motion } from 'framer-motion';
import { ConversationProvider, useConversation } from '@/conversation/ConversationContext';
import { ConversationFeed } from '@/conversation/ConversationFeed';
import { Composer } from '@/conversation/Composer';
import { ContextStrip } from '@/conversation/ContextStrip';
import { AuthProvider, useAuth } from '@/auth/AuthContext';
import { AuthGateBridge } from '@/auth/AuthGateBridge';
import { ProfileMenu } from './ProfileMenu';
import { GeminiStar } from './GeminiStar';
import { ResumeStage } from './ResumeStage';
import { cn } from '@/lib/cn';

/**
 * Single unified surface for the whole app.
 *
 *   ┌──────────────────────────────────────────────────────────┐
 *   │                      ✦                  [ profile chip ] │
 *   │       [ 📄 resume.pdf ] [ 🎯 acme.com ] [ 💼 Mid ]       │  ← context strip
 *   │                                                          │
 *   │                                                          │
 *   │                 Hi — I'm your resume                     │
 *   │                  co-pilot. Ready?                        │  ← centered hero
 *   │                                                          │
 *   │                                                          │
 *   │              [ pill ]  [ pill ]  [ pill ]                │  ← choices
 *   │         ┌────────────────────────────────────┐           │
 *   │         │ +   Ask your co-pilot…   Fast  🎤 │           │  ← composer
 *   │         └────────────────────────────────────┘           │
 *   └──────────────────────────────────────────────────────────┘
 *
 * Only ever one agent turn is on the stage at a time. Accumulated
 * collected data is surfaced via <ContextStrip/> below the header.
 */
export function AppShell() {
  return (
    <AuthProvider>
      <ConversationProvider>
        <AuthGateBridge />
        <ShellChrome />
      </ConversationProvider>
    </AuthProvider>
  );
}

function ShellChrome() {
  // Phase drives layout variations. Phases 1/2 keep a single centered column;
  // Phase 5 (REVIEWING) will split to feed-left / stage-right.
  const { state } = useConversation();
  const { user, bypassMode } = useAuth();
  const isReviewing = state.phase === 'REVIEWING';

  return (
    <div className={cn('shell-gradient relative w-full overflow-hidden text-ink-900', isReviewing ? 'h-dvh' : 'min-h-dvh')}>
      {/* Top chrome: profile (right) + subtle brand star (center) */}
      <header className="pointer-events-none absolute inset-x-0 top-0 z-20 flex items-center justify-between p-4 sm:p-6">
        <div className="w-20" aria-hidden="true" />
        <div className="pointer-events-none">
          <GeminiStar
            className="h-5 w-5 opacity-80"
            animate={state.phase === 'PROCESSING'}
          />
        </div>
        <div className="pointer-events-auto flex w-20 justify-end">
          <ProfileMenu
            user={
              user
                ? {
                    name:
                      (
                        bypassMode
                          ? `${(user.user_metadata?.full_name as string | undefined) ?? 'Dev User'} (bypass)`
                          : (user.user_metadata?.full_name as string | undefined)
                      ) ??
                      user.email ??
                      undefined,
                    email: user.email ?? undefined,
                  }
                : null
            }
          />
        </div>
      </header>

      {/* Context chips below header — absolute so they never push the
          center stage off-axis, no matter how many are collected. */}
      <div
        className={cn(
          'pointer-events-none absolute inset-x-0 z-10 flex justify-center px-4',
          'top-14 sm:top-[72px]',
        )}
      >
        <div className="pointer-events-auto">
          <ContextStrip data={state.data} />
        </div>
      </div>

      {/*
        Main grid. Two layouts sharing one container so Framer's `layout`
        prop on the chat column can smoothly animate its width from the
        pre-reveal centered column to the reviewing-state left pane.

          Non-reviewing →  [       chat (centered)       ]
          Reviewing     →  [ chat | resume stage         ]
       */}
      <motion.main
        layout
        transition={{ duration: 0.65, ease: [0.2, 0.7, 0.2, 1] }}
        className={cn(
          'relative mx-auto grid w-full',
          'px-5 sm:px-8',
          isReviewing
            ? 'h-dvh max-w-[110rem] grid-cols-1 gap-6 overflow-hidden lg:grid-cols-[minmax(340px,32rem)_1fr] lg:gap-8'
            : 'min-h-dvh max-w-2xl grid-cols-1',
        )}
      >
        {/* Chat column — always present, shrinks to the left in reviewing. */}
        <motion.section
          layout
          transition={{ duration: 0.65, ease: [0.2, 0.7, 0.2, 1] }}
          className={cn(
            'relative flex flex-col pt-28 sm:pt-36',
            isReviewing ? 'h-full overflow-hidden' : 'min-h-dvh pb-52',
          )}
        >
          <div
            className={cn(
              'flex w-full flex-1',
              isReviewing
                ? 'min-h-0 items-start justify-start overflow-y-auto pb-6'
                : 'items-center justify-center',
            )}
          >
            <ConversationFeed />
          </div>

          {/* In-column composer — only mounts in reviewing mode. */}
          {isReviewing && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.55, ease: [0.2, 0.7, 0.2, 1] }}
              className="shrink-0 z-20 w-full pb-4 pt-2"
            >
              <Composer />
            </motion.div>
          )}
        </motion.section>

        {/* Stage column — the optimized resume as a piece of paper. */}
        <AnimatePresence>
          {isReviewing && state.data.review && (
            <motion.section
              key="stage"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.4 }}
              className="relative flex h-full flex-col overflow-hidden pt-28 sm:pt-36"
            >
              <ResumeStage resume={state.data.review.resume} />
            </motion.section>
          )}
        </AnimatePresence>
      </motion.main>

      {/* Bottom-locked composer — only in pre-reveal phases. */}
      {!isReviewing && (
        <div className="pointer-events-none fixed inset-x-0 bottom-0 z-30">
          <div className="pointer-events-auto mx-auto w-full max-w-2xl px-5 pb-6 sm:px-8 sm:pb-8">
            <Composer />
          </div>
        </div>
      )}
    </div>
  );
}
