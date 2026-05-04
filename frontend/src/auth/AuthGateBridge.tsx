import { useEffect, useRef } from 'react';
import { useAuth } from './AuthContext';
import { useConversation } from '@/conversation/ConversationContext';

/**
 * Invisible bridge that advances the conversation out of the AUTH_GATE
 * phase as soon as the user becomes authenticated. Lives inside
 * <AppShell/> because it needs access to both `AuthContext` and
 * `ConversationContext`.
 */
export function AuthGateBridge() {
  const { state, submit } = useConversation();
  const { isAuthenticated, loading, user } = useAuth();
  const advancedForRef = useRef<string | null>(null);

  useEffect(() => {
    if (loading) return;
    if (state.phase !== 'AUTH_GATE') return;
    if (!isAuthenticated) return;

    // Only advance once per signed-in session.
    const key = user?.id ?? 'authenticated';
    if (advancedForRef.current === key) return;
    advancedForRef.current = key;

    submit({ text: 'Signed in', choiceValue: 'signed_in' });
  }, [state.phase, isAuthenticated, loading, user?.id, submit]);

  return null;
}
