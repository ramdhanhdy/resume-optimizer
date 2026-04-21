import { cn } from '@/lib/cn';

interface GeminiStarProps {
  className?: string;
  /** Render as a solid multi-color glyph, or a softer monochrome sky-blue. */
  variant?: 'color' | 'mono';
  /** Enable a gentle twinkle animation (used during PROCESSING). */
  animate?: boolean;
}

/**
 * Four-point sparkle glyph used as the agent's identity mark — shown at
 * top-center of the shell and inline during processing.
 */
export function GeminiStar({ className, variant = 'color', animate }: GeminiStarProps) {
  if (variant === 'mono') {
    return (
      <svg
        viewBox="0 0 24 24"
        className={cn('text-sky-500', animate && 'orb-pulse', className)}
        fill="currentColor"
        aria-hidden="true"
      >
        <path d="M12 2c.4 3.6 1.6 6 3.1 7.5C16.7 11 19 12.2 22.6 12.6c-3.6.4-6 1.6-7.5 3.1C13.6 17.2 12.4 19.5 12 23c-.4-3.5-1.6-5.8-3.1-7.3C7.4 14.2 5 13 1.4 12.6 5 12.2 7.4 11 8.9 9.5 10.4 8 11.6 5.6 12 2z" />
      </svg>
    );
  }

  // Multi-color Gemini-style sparkle: one large 4-point diamond with a
  // smaller accent diamond offset to the side, tinted with Google hues.
  return (
    <svg
      viewBox="0 0 48 48"
      className={cn(animate && 'orb-pulse', className)}
      aria-hidden="true"
    >
      <defs>
        <linearGradient id="gs-main" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="var(--color-star-blue)" />
          <stop offset="55%" stopColor="var(--color-star-red)" />
          <stop offset="100%" stopColor="var(--color-star-yellow)" />
        </linearGradient>
        <linearGradient id="gs-accent" x1="0" y1="1" x2="1" y2="0">
          <stop offset="0%" stopColor="var(--color-star-yellow)" />
          <stop offset="100%" stopColor="var(--color-star-green)" />
        </linearGradient>
      </defs>
      {/* Main 4-point diamond */}
      <path
        fill="url(#gs-main)"
        d="M24 4c.9 7.6 3.6 12.6 7.1 16.1C34.6 23.6 39.6 26.3 47 27c-7.4.7-12.4 3.4-15.9 6.9C27.6 37.4 24.9 42.4 24 50c-.9-7.6-3.6-12.6-7.1-16.1C13.4 30.4 8.4 27.7 1 27c7.4-.7 12.4-3.4 15.9-6.9C20.4 16.6 23.1 11.6 24 4z"
        transform="translate(0 -2) scale(0.92) translate(1 1)"
      />
      {/* Smaller accent sparkle, offset */}
      <path
        fill="url(#gs-accent)"
        d="M38 8c.3 2.6 1.2 4.3 2.4 5.5C41.6 14.7 43.3 15.6 46 16c-2.7.4-4.4 1.3-5.6 2.5C39.2 19.7 38.3 21.4 38 24c-.3-2.6-1.2-4.3-2.4-5.5C34.4 17.3 32.7 16.4 30 16c2.7-.4 4.4-1.3 5.6-2.5C36.8 12.3 37.7 10.6 38 8z"
        opacity="0.95"
      />
    </svg>
  );
}
