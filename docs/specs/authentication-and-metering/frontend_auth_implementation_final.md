# Frontend Supabase Auth Implementation Specification (Final)

## 1. Overview
This document specifies the final implementation plan for integrating Supabase Authentication into the Resume Optimizer React application. It combines the UI/UX implementation details from the Claude plan with the architectural robustness (SSE/EventSource handling) of the Codex plan.

## 2. Dependencies & Setup

### Package.json
Install the Supabase client library:
```bash
npm install @supabase/supabase-js
```

### Environment Variables
**File:** `.env` (and `.env.example`)
```bash
# Supabase Configuration
VITE_SUPABASE_URL=https://<your-project>.supabase.co
VITE_SUPABASE_ANON_KEY=eyJ...

# Backend API URL
VITE_API_URL=http://localhost:8000

# Optional: OAuth Redirect URL (if needed for specific flows)
VITE_SUPABASE_REDIRECT_URL=http://localhost:5173/auth/callback
```

## 3. Core Infrastructure

### 3.1 Supabase Client
**File:** `src/lib/supabase.ts`
Initializes the Supabase client with safe defaults.
```typescript
import { createClient } from '@supabase/supabase-js';

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL;
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY;

if (!supabaseUrl || !supabaseAnonKey) {
  throw new Error('Missing Supabase environment variables');
}

export const supabase = createClient(supabaseUrl, supabaseAnonKey, {
  auth: {
    autoRefreshToken: true,
    persistSession: true,
    detectSessionInUrl: true,
  },
});
```

### 3.2 Auth Context Provider
**File:** `src/contexts/AuthContext.tsx`
Manages global auth state, handles multi-tab synchronization, and provides helper methods.

**Key Requirements:**
- **State:** `user`, `session`, `loading`
- **Actions:** `signInWithEmail`, `signUpWithEmail`, `signInWithOAuth`, `signOut`, `getToken`
- **Listeners:** Subscribe to `onAuthStateChange` to handle token refreshes and multi-tab state changes.

```typescript
import { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { Session, User, AuthError } from '@supabase/supabase-js';
import { supabase } from '@/lib/supabase';

interface AuthContextType {
  user: User | null;
  session: Session | null;
  loading: boolean;
  signInWithEmail: (email: string, password: string) => Promise<{ error: AuthError | null }>;
  signUpWithEmail: (email: string, password: string) => Promise<{ error: AuthError | null }>;
  signInWithOAuth: (provider: 'google' | 'github') => Promise<void>;
  signOut: () => Promise<void>;
  getToken: () => Promise<string | null>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [session, setSession] = useState<Session | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Initial session check
    supabase.auth.getSession().then(({ data: { session } }) => {
      setSession(session);
      setUser(session?.user ?? null);
      setLoading(false);
    });

    // Real-time auth state listener
    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      (_event, session) => {
        setSession(session);
        setUser(session?.user ?? null);
        setLoading(false);
      }
    );

    return () => subscription.unsubscribe();
  }, []);

  const getToken = async () => {
    const { data } = await supabase.auth.getSession();
    return data.session?.access_token ?? null;
  };

  // ... implementation of signIn/signUp/signOut wrappers ...
  // See src/lib/supabase.ts for supabase calls

  return (
    <AuthContext.Provider value={{
      user, session, loading,
      signInWithEmail, signUpWithEmail, signInWithOAuth, signOut, getToken
    }}>
      {children}
    </AuthContext.Provider>
  );
}
```

## 4. Data Layer & Streaming

### 4.1 API Client Update
**File:** `src/services/api.ts`
Modifies the `ApiClient` to inject the Bearer token into headers.

**Key Changes:**
- **Authorization Header:** `Authorization: Bearer <token>`
- **Error Handling:** Catch `402 Payment Required` and throw a specific `UsageLimitError`.

```typescript
// Snippet for request method
private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const token = (await supabase.auth.getSession()).data.session?.access_token;
  const headers = {
    'Content-Type': 'application/json',
    ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
    ...options.headers,
  };
  
  // ... fetch and error handling ...
  if (response.status === 402) {
    throw new UsageLimitError('Usage limit reached', 0);
  }
}
```

### 4.2 Streaming Hook (Critical)
**File:** `src/hooks/useProcessingJob.ts`
The native `EventSource` API does not support custom headers. We must pass the access token via a URL query parameter for the streaming endpoint.

**Implementation Logic:**
```typescript
const startStream = async (jobId: string) => {
  const { data } = await supabase.auth.getSession();
  const token = data.session?.access_token;

  if (!token) throw new Error("Unauthorized");

  // Pass token in URL query param for EventSource
  const streamUrl = `${API_BASE_URL}/api/stream/${jobId}?access_token=${encodeURIComponent(token)}`;
  
  const eventSource = new EventSource(streamUrl);
  
  eventSource.onmessage = (event) => { /* handle data */ };
  
  eventSource.onerror = (err) => {
    // Check for auth errors (will appear as connection failure)
    // Close and handle appropriately
    eventSource.close();
  };
};
```

## 5. User Interface

### 5.1 App Component
**File:** `src/App.tsx`
Wraps the application with `AuthProvider` and implements the high-level auth gate.
- If `loading`: Show `LoadingSpinner`.
- If `!user`: Show `LoginScreen`.
- If `user`: Show `InputScreen` (or current app state).
- Handle `/auth/callback` route for OAuth redirects.

### 5.2 Login Screen
**File:** `src/components/auth/LoginScreen.tsx`
A polished UI component using existing design system (Tailwind + Framer Motion).
- **Modes:** Login / Signup toggles.
- **Inputs:** Email, Password.
- **Social:** Google, GitHub buttons.
- **Copy:** "Start with 5 free resume optimizations".

### 5.3 Usage Meter
**File:** `src/components/shared/UsageMeter.tsx`
A component to display the user's remaining quota.
- Uses `useUsage` hook to fetch quota from backend.
- Displays generic "X/5 free" progress bar.
- Shows "Pro Plan" badge if `is_subscribed` is true.

## 6. Migration Strategy

1.  **Phase 1: Setup**
    - Install dependencies.
    - Set up `.env` variables.
    - Create `supabase.ts` and `AuthContext.tsx`.

2.  **Phase 2: UI Implementation**
    - Create `LoginScreen.tsx` and `UsageMeter.tsx`.
    - Update `App.tsx` to wrap with AuthProvider and gate access.

3.  **Phase 3: Integration**
    - Update `api.ts` to attach Bearer tokens.
    - Update `useProcessingJob.ts` to use URL-param auth for SSE.
    - (Backend must support `access_token` query param for streaming endpoint).

4.  **Phase 4: Cleanup**
    - Remove legacy `X-Client-Id` logic once backend fully enforces JWT.
    - Remove `src/utils/clientId.ts`.

## 7. Security Considerations
- **Anon Key Only:** Never expose `service_role` key in frontend.
- **Token Handling:** Do not store tokens in `localStorage` manually; let Supabase SDK handle persistence.
- **HTTPS:** Ensure production runs on HTTPS for secure token transmission.
