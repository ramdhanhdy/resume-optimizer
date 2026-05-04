import { useEffect } from 'react';
import { GeminiStar } from '@/shell/GeminiStar';

export function AuthCallback() {
  useEffect(() => {
    // Supabase handles the OAuth callback automatically via detectSessionInUrl.
    // Just redirect to home after a brief delay to allow session to be set.
    const timer = setTimeout(() => {
      window.location.replace('/');
    }, 1500);

    return () => clearTimeout(timer);
  }, []);

  return (
    <div className="shell-gradient min-h-dvh flex flex-col items-center justify-center">
      <GeminiStar className="h-8 w-8 text-sky-400 opacity-80" animate={true} />
      <p className="mt-4 text-sm text-ink-500 font-medium tracking-wide">Completing sign in…</p>
    </div>
  );
}
