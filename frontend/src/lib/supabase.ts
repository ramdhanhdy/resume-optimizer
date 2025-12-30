import { createClient } from '@supabase/supabase-js';

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL;

// Prefer new publishable key format (sb_publishable_...), fall back to legacy anon key
const supabaseKey = import.meta.env.VITE_SUPABASE_PUBLISHABLE_KEY || import.meta.env.VITE_SUPABASE_ANON_KEY;

if (!supabaseUrl || !supabaseKey) {
  console.error('Missing Supabase environment variables:', { 
    supabaseUrl, 
    hasPublishableKey: !!import.meta.env.VITE_SUPABASE_PUBLISHABLE_KEY,
    hasAnonKey: !!import.meta.env.VITE_SUPABASE_ANON_KEY 
  });
  throw new Error('Missing Supabase environment variables. Set VITE_SUPABASE_PUBLISHABLE_KEY (preferred) or VITE_SUPABASE_ANON_KEY (legacy)');
}

console.log('Initializing Supabase client with URL:', supabaseUrl);

export const supabase = createClient(supabaseUrl, supabaseKey, {
  auth: {
    autoRefreshToken: true,
    persistSession: true,
    detectSessionInUrl: true,
  },
});
