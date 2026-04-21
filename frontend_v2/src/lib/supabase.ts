import { createClient, type SupabaseClient } from '@supabase/supabase-js';

/**
 * Supabase client — initialized lazily from env vars. When the env vars are
 * missing (e.g. you're running frontend_v2 locally without creds), the
 * client is `null` and consumers must fall back to the dev bypass path.
 *
 *   VITE_SUPABASE_URL
 *   VITE_SUPABASE_PUBLISHABLE_KEY   (preferred, modern)
 *   VITE_SUPABASE_ANON_KEY          (legacy fallback)
 */
const supabaseUrl = import.meta.env.VITE_SUPABASE_URL as string | undefined;
const supabaseKey =
  (import.meta.env.VITE_SUPABASE_PUBLISHABLE_KEY as string | undefined) ||
  (import.meta.env.VITE_SUPABASE_ANON_KEY as string | undefined);

export const supabaseConfigured = Boolean(supabaseUrl && supabaseKey);

export const supabase: SupabaseClient | null = supabaseConfigured
  ? createClient(supabaseUrl!, supabaseKey!, {
      auth: {
        autoRefreshToken: true,
        persistSession: true,
        detectSessionInUrl: true,
      },
    })
  : null;

if (!supabaseConfigured) {
  // eslint-disable-next-line no-console
  console.info(
    '[supabase] VITE_SUPABASE_URL / VITE_SUPABASE_PUBLISHABLE_KEY are not set. ' +
      'Auth will fall back to dev-bypass mode if VITE_AUTH_BYPASS=true.',
  );
}
