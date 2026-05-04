import { useState } from 'react';
import { motion } from 'framer-motion';
import { Loader2 } from 'lucide-react';
import { useAuth } from '@/auth/AuthContext';
import { cn } from '@/lib/cn';

interface AuthPillsProps {
  providers: Array<'google' | 'email'>;
  /** Retained for API compatibility. With real auth wired in, the
   *  AuthGateBridge handles advancing once `isAuthenticated` flips true,
   *  so callers rarely need this. */
  onPick?: (provider: 'google' | 'email') => void;
  disabled?: boolean;
}

/**
 * Floating auth options. Wired to the real `AuthContext` — clicking
 * "Continue with Google" either triggers Supabase OAuth (real mode) or
 * resolves to a synthetic dev user (bypass mode).
 *
 * Advancing the conversation on auth success is handled by the
 * <AuthGateBridge/> in `AppShell`, which watches `isAuthenticated` and
 * calls `submit()` once the session lands.
 */
export function AuthPills({ providers, onPick, disabled }: AuthPillsProps) {
  const { signInWithOAuth, bypassMode } = useAuth();
  const [pending, setPending] = useState<'google' | 'email' | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleGoogle = async () => {
    setPending('google');
    setError(null);
    try {
      await signInWithOAuth('google');
      onPick?.('google');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Sign-in failed. Please try again.');
      setPending(null);
    }
    // In bypass mode the AuthContext flips `user` synchronously once the
    // short delay resolves, and the bridge takes over. In real OAuth mode
    // the browser redirects away, so we leave `pending` set.
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: 6 }}
      className="flex flex-col items-center gap-2"
    >
      <div className="flex flex-wrap justify-center gap-2">
        {providers.includes('google') && (
          <motion.button
            type="button"
            disabled={disabled || pending !== null}
            whileHover={{ y: -2 }}
            whileTap={{ scale: 0.96 }}
            onClick={handleGoogle}
            className={cn(
              'inline-flex items-center gap-2 rounded-full glass-sky px-4 py-2 text-[14px]',
              'text-ink-900 soft-shadow ring-1 ring-sky-200/60 transition',
              'hover:ring-sky-300',
              'disabled:opacity-60 disabled:pointer-events-none',
            )}
          >
            {pending === 'google' ? (
              <Loader2 className="h-4 w-4 animate-spin text-ink-500" strokeWidth={1.75} />
            ) : (
              <GoogleGlyph />
            )}
            <span className="font-medium">
              {pending === 'google' ? 'Signing you in…' : 'Continue with Google'}
            </span>
          </motion.button>
        )}
      </div>
      {bypassMode && (
        <span className="text-[11px] text-ink-400">
          Dev-bypass mode · no real account required
        </span>
      )}
      {error && (
        <span className="max-w-[320px] text-center text-[12px] text-red-500">
          {error}
        </span>
      )}
    </motion.div>
  );
}

function GoogleGlyph() {
  return (
    <svg className="h-4 w-4" viewBox="0 0 24 24" aria-hidden="true">
      <path
        fill="#EA4335"
        d="M12 10.2v3.9h5.4c-.24 1.44-1.7 4.2-5.4 4.2-3.25 0-5.9-2.7-5.9-6s2.65-6 5.9-6c1.85 0 3.1.78 3.8 1.46l2.6-2.5C16.8 3.8 14.6 2.8 12 2.8 6.9 2.8 2.8 6.9 2.8 12s4.1 9.2 9.2 9.2c5.3 0 8.8-3.72 8.8-8.97 0-.6-.07-1.06-.16-1.5H12z"
      />
    </svg>
  );
}
