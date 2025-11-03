/**
 * useMediaQuery Hook
 *
 * React hook for responsive design based on media queries.
 * Syncs with CSS breakpoints and provides TypeScript-safe queries.
 */

import { useState, useEffect } from 'react';
import { breakpoints } from '@/design-system/tokens/spacing';

/**
 * Hook to match media queries
 * @param query - Media query string (e.g., "(min-width: 768px)")
 * @returns boolean - true if media query matches
 *
 * @example
 * const isDesktop = useMediaQuery('(min-width: 1024px)');
 */
export function useMediaQuery(query: string): boolean {
  // Default to false for SSR
  const [matches, setMatches] = useState(false);

  useEffect(() => {
    // Check if window.matchMedia is available
    if (typeof window === 'undefined' || !window.matchMedia) {
      return;
    }

    // Create media query
    const mediaQuery = window.matchMedia(query);

    // Set initial value
    setMatches(mediaQuery.matches);

    // Create event handler
    const handleChange = (event: MediaQueryListEvent) => {
      setMatches(event.matches);
    };

    // Add event listener
    if (mediaQuery.addEventListener) {
      mediaQuery.addEventListener('change', handleChange);
    } else {
      // @ts-ignore - deprecated but needed for older browsers
      mediaQuery.addListener(handleChange);
    }

    // Cleanup
    return () => {
      if (mediaQuery.removeEventListener) {
        mediaQuery.removeEventListener('change', handleChange);
      } else {
        // @ts-ignore - deprecated but needed for older browsers
        mediaQuery.removeListener(handleChange);
      }
    };
  }, [query]);

  return matches;
}

/**
 * Breakpoint-specific hooks for common responsive patterns
 */

/**
 * Check if viewport is at least 640px (sm breakpoint)
 */
export function useIsSmallScreen(): boolean {
  return useMediaQuery(`(min-width: ${breakpoints.sm})`);
}

/**
 * Check if viewport is at least 768px (md breakpoint)
 */
export function useIsMediumScreen(): boolean {
  return useMediaQuery(`(min-width: ${breakpoints.md})`);
}

/**
 * Check if viewport is at least 1024px (lg breakpoint)
 */
export function useIsLargeScreen(): boolean {
  return useMediaQuery(`(min-width: ${breakpoints.lg})`);
}

/**
 * Check if viewport is at least 1280px (xl breakpoint)
 */
export function useIsExtraLargeScreen(): boolean {
  return useMediaQuery(`(min-width: ${breakpoints.xl})`);
}

/**
 * Check if viewport is mobile (less than md breakpoint)
 */
export function useIsMobile(): boolean {
  return !useMediaQuery(`(min-width: ${breakpoints.md})`);
}

/**
 * Check if viewport is tablet (between md and lg)
 */
export function useIsTablet(): boolean {
  const isMd = useMediaQuery(`(min-width: ${breakpoints.md})`);
  const isLg = useMediaQuery(`(min-width: ${breakpoints.lg})`);
  return isMd && !isLg;
}

/**
 * Check if viewport is desktop (lg or larger)
 */
export function useIsDesktop(): boolean {
  return useMediaQuery(`(min-width: ${breakpoints.lg})`);
}

/**
 * Get current breakpoint name
 * @returns Breakpoint name or 'xs' for smallest
 */
export function useBreakpoint(): 'xs' | 'sm' | 'md' | 'lg' | 'xl' | '2xl' {
  const is2xl = useMediaQuery(`(min-width: ${breakpoints['2xl']})`);
  const isXl = useMediaQuery(`(min-width: ${breakpoints.xl})`);
  const isLg = useMediaQuery(`(min-width: ${breakpoints.lg})`);
  const isMd = useMediaQuery(`(min-width: ${breakpoints.md})`);
  const isSm = useMediaQuery(`(min-width: ${breakpoints.sm})`);

  if (is2xl) return '2xl';
  if (isXl) return 'xl';
  if (isLg) return 'lg';
  if (isMd) return 'md';
  if (isSm) return 'sm';
  return 'xs';
}

/**
 * Check if device supports hover (not touch-only)
 */
export function useHasHover(): boolean {
  return useMediaQuery('(hover: hover) and (pointer: fine)');
}

/**
 * Check if device is touch-capable
 */
export function useIsTouchDevice(): boolean {
  return useMediaQuery('(pointer: coarse)');
}

/**
 * Check if user prefers dark mode
 */
export function usePrefersColorScheme(): 'light' | 'dark' {
  const prefersDark = useMediaQuery('(prefers-color-scheme: dark)');
  return prefersDark ? 'dark' : 'light';
}

/**
 * Check orientation
 */
export function useOrientation(): 'portrait' | 'landscape' {
  const isPortrait = useMediaQuery('(orientation: portrait)');
  return isPortrait ? 'portrait' : 'landscape';
}
