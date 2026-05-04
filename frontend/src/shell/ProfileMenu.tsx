import { useEffect, useRef, useState } from 'react';
import { ChevronDown, LogOut, User, History, Settings } from 'lucide-react';
import { useAuth } from '@/auth/AuthContext';
import { cn } from '@/lib/cn';

interface ProfileMenuProps {
  /** Null when signed out. */
  user?: { email?: string; name?: string } | null;
  className?: string;
  onOpenHistory?: () => void;
  onOpenSettings?: () => void;
}

/**
 * Minimal, semi-transparent profile menu anchored top-right.
 * Shows account status and exposes real sign-out when authenticated.
 */
export function ProfileMenu({ user, className, onOpenHistory, onOpenSettings }: ProfileMenuProps) {
  const { signOut } = useAuth();
  const [open, setOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement | null>(null);
  const label = user?.name || user?.email || 'Sign in';
  const signedIn = Boolean(user);

  useEffect(() => {
    if (!open) return;

    const onPointerDown = (event: PointerEvent) => {
      if (!menuRef.current?.contains(event.target as Node)) {
        setOpen(false);
      }
    };

    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') setOpen(false);
    };

    document.addEventListener('pointerdown', onPointerDown);
    document.addEventListener('keydown', onKeyDown);
    return () => {
      document.removeEventListener('pointerdown', onPointerDown);
      document.removeEventListener('keydown', onKeyDown);
    };
  }, [open]);

  const handleSignOut = async () => {
    await signOut();
    setOpen(false);
  };

  const handleAction = (action?: () => void) => {
    action?.();
    setOpen(false);
  };

  return (
    <div ref={menuRef} className={cn('relative', className)}>
      <button
        type="button"
        className={cn(
          'glass rounded-full px-2.5 py-1 text-[13px] text-ink-600',
          'flex items-center gap-2 ring-1 ring-white/70 transition',
          'hover:bg-white/70 hover:text-ink-800 focus:outline-none focus:ring-2 focus:ring-sky-300/70',
        )}
        title={signedIn ? `Account: ${label}` : 'Sign in status'}
        aria-haspopup="menu"
        aria-expanded={open}
        onClick={() => setOpen((current) => !current)}
      >
        <span
          className={cn(
            'flex h-6 w-6 items-center justify-center rounded-full',
            signedIn
              ? 'bg-gradient-to-br from-sky-300 to-sky-500 text-white'
              : 'bg-white/70 text-ink-500',
          )}
        >
          <User className="h-3.5 w-3.5" strokeWidth={2.25} />
        </span>
        <span className="hidden max-w-[14ch] truncate sm:inline-block">
          {label}
        </span>
        <ChevronDown
          className={cn('hidden h-3.5 w-3.5 transition sm:block', open && 'rotate-180')}
          strokeWidth={2}
        />
      </button>

      {open && (
        <div
          role="menu"
          className={cn(
            'glass absolute right-0 mt-2 w-56 overflow-hidden rounded-2xl p-1.5 text-[13px]',
            'soft-shadow-lg ring-1 ring-white/70 flex flex-col',
          )}
        >
          <div className="px-3 py-2 text-ink-500 mb-1 border-b border-ink-200/50">
            <div className="font-medium text-ink-800">
              {signedIn ? 'Signed in' : 'Not signed in'}
            </div>
            {user?.email && (
              <div className="truncate text-[12px]" title={user.email}>
                {user.email}
              </div>
            )}
          </div>

          {signedIn && (
            <>
              <button
                type="button"
                role="menuitem"
                onClick={() => handleAction(onOpenHistory)}
                className={cn(
                  'flex w-full items-center gap-2 rounded-xl px-3 py-2 text-left text-ink-700 transition',
                  'hover:bg-white/70 hover:text-ink-900 focus:outline-none focus:ring-2 focus:ring-sky-300/60',
                )}
              >
                <History className="h-4 w-4" strokeWidth={2} />
                History
              </button>
              
              <button
                type="button"
                role="menuitem"
                onClick={() => handleAction(onOpenSettings)}
                className={cn(
                  'flex w-full items-center gap-2 rounded-xl px-3 py-2 text-left text-ink-700 transition',
                  'hover:bg-white/70 hover:text-ink-900 focus:outline-none focus:ring-2 focus:ring-sky-300/60',
                )}
              >
                <Settings className="h-4 w-4" strokeWidth={2} />
                Settings
              </button>

              <div className="my-1 h-px w-full bg-ink-200/50" />

              <button
                type="button"
                role="menuitem"
                onClick={handleSignOut}
                className={cn(
                  'flex w-full items-center gap-2 rounded-xl px-3 py-2 text-left text-ink-700 transition',
                  'hover:bg-white/70 hover:text-red-600 focus:outline-none focus:ring-2 focus:ring-red-300/60',
                )}
              >
                <LogOut className="h-4 w-4" strokeWidth={2} />
                Sign out
              </button>
            </>
          )}
        </div>
      )}
    </div>
  );
}
