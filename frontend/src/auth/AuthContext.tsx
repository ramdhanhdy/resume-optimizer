import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react';
import type { Session, User } from '@supabase/supabase-js';
import { supabase } from '@/lib/supabase';

/**
 * Thin wrapper around the Supabase auth client. Mirrors the shape of the
 * legacy `frontend/src/contexts/AuthContext.tsx` so existing helpers are
 * drop-in compatible.
 *
 * Dev bypass: when `VITE_AUTH_BYPASS=true`,
 * clicking "Continue with Google" in the UI immediately resolves to a
 * synthetic local user so the rest of the conversational flow (Phase 4)
 * can be exercised without real credentials.
 */

interface AuthContextType {
  user: User | null;
  session: Session | null;
  loading: boolean;
  isAuthenticated: boolean;
  /** True if we're running without real Supabase creds. */
  bypassMode: boolean;
  signInWithOAuth: (provider: 'google' | 'github') => Promise<void>;
  signOut: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const BYPASS_ENABLED =
  (import.meta.env.VITE_AUTH_BYPASS as string | undefined) === 'true';

const DEV_USER: User = {
  id: 'dev-bypass-user',
  aud: 'authenticated',
  role: 'authenticated',
  email: 'dev@local',
  app_metadata: { provider: 'bypass' },
  user_metadata: { full_name: 'Dev User' },
  created_at: new Date().toISOString(),
} as unknown as User;

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [session, setSession] = useState<Session | null>(null);
  const [loading, setLoading] = useState(!BYPASS_ENABLED);

  // Real Supabase listener — only runs when a client is configured.
  useEffect(() => {
    if (!supabase) {
      setLoading(false);
      return;
    }

    let cancelled = false;
    const timeoutId = setTimeout(() => {
      if (!cancelled) setLoading(false);
    }, 5000);

    supabase.auth
      .getSession()
      .then(({ data }) => {
        if (cancelled) return;
        clearTimeout(timeoutId);
        setSession(data.session);
        setUser(data.session?.user ?? null);
        setLoading(false);
      })
      .catch(() => {
        if (!cancelled) {
          clearTimeout(timeoutId);
          setLoading(false);
        }
      });

    const { data: sub } = supabase.auth.onAuthStateChange((_e, s) => {
      if (cancelled) return;
      setSession(s);
      setUser(s?.user ?? null);
      setLoading(false);
    });

    return () => {
      cancelled = true;
      clearTimeout(timeoutId);
      sub.subscription.unsubscribe();
    };
  }, []);

  const signInWithOAuth = useCallback(async (provider: 'google' | 'github') => {
    if (BYPASS_ENABLED) {
      // Short delay so the UI transition feels deliberate.
      await new Promise((r) => setTimeout(r, 600));
      setUser(DEV_USER);
      setSession({ user: DEV_USER } as Session);
      return;
    }
    if (!supabase) {
      throw new Error('Supabase auth is not configured. Set VITE_SUPABASE_URL and VITE_SUPABASE_PUBLISHABLE_KEY, or enable VITE_AUTH_BYPASS=true for local bypass.');
    }
    await supabase.auth.signInWithOAuth({
      provider,
      options: { redirectTo: `${window.location.origin}/auth/callback` },
    });
  }, []);

  const signOut = useCallback(async () => {
    if (supabase && !BYPASS_ENABLED) {
      await supabase.auth.signOut();
    }
    setUser(null);
    setSession(null);
  }, []);

  const value = useMemo<AuthContextType>(
    () => ({
      user,
      session,
      loading,
      isAuthenticated: !!user,
      bypassMode: BYPASS_ENABLED,
      signInWithOAuth,
      signOut,
    }),
    [user, session, loading, signInWithOAuth, signOut],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextType {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within an AuthProvider');
  return ctx;
}
