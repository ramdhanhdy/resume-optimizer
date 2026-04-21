import { User } from 'lucide-react';
import { cn } from '@/lib/cn';

interface ProfileMenuProps {
  /** Null when signed out (Phase 1 always). */
  user?: { email?: string; name?: string } | null;
  className?: string;
}

/**
 * Minimal, semi-transparent profile chip anchored top-right.
 * Phase 1: renders a "Sign in" hint only. Real auth plugs in during Phase 3.
 */
export function ProfileMenu({ user, className }: ProfileMenuProps) {
  const label = user?.name || user?.email || 'Sign in';

  return (
    <button
      type="button"
      className={cn(
        'glass rounded-full px-2.5 py-1 text-[13px] text-ink-600',
        'flex items-center gap-2 transition',
        'hover:text-ink-900 ring-1 ring-white/70',
        'hover:ring-sky-200',
        className,
      )}
      aria-label={user ? `Account: ${label}` : 'Sign in'}
    >
      <span
        className={cn(
          'flex h-6 w-6 items-center justify-center rounded-full',
          'bg-gradient-to-br from-sky-300 to-sky-500 text-white',
        )}
      >
        <User className="h-3.5 w-3.5" strokeWidth={2.25} />
      </span>
      <span className="hidden max-w-[12ch] truncate sm:inline-block">
        {label}
      </span>
    </button>
  );
}
