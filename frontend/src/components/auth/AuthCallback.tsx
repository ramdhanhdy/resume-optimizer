import { useEffect } from 'react';
import { Loader2 } from 'lucide-react';

export default function AuthCallback() {
  useEffect(() => {
    // Supabase handles the OAuth callback automatically via detectSessionInUrl
    // Just redirect to home after a brief delay to allow session to be set
    const timer = setTimeout(() => {
      window.location.href = '/';
    }, 1000);

    return () => clearTimeout(timer);
  }, []);

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-gradient-to-br from-[#FAF9F6] via-[#F5F3EE] to-[#EEF2F1]">
      <Loader2 className="w-8 h-8 animate-spin text-accent mb-4" />
      <p className="text-text-main/60">Completing sign in...</p>
    </div>
  );
}
