/**
 * Design System - Reduced Motion Hook
 *
 * React hook that respects user's motion preferences.
 * Returns true if user prefers reduced motion.
 */

import { useState, useEffect } from 'react';

/**
 * Hook to detect user's motion preference
 * @returns boolean - true if user prefers reduced motion
 *
 * @example
 * const prefersReducedMotion = useReducedMotion();
 * const animationDuration = prefersReducedMotion ? 0 : 300;
 */
export function useReducedMotion(): boolean {
  // Default to false for SSR
  const [prefersReducedMotion, setPrefersReducedMotion] = useState(false);

  useEffect(() => {
    // Check if window.matchMedia is available
    if (typeof window === 'undefined' || !window.matchMedia) {
      return;
    }

    // Create media query
    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');

    // Set initial value
    setPrefersReducedMotion(mediaQuery.matches);

    // Create event handler
    const handleChange = (event: MediaQueryListEvent) => {
      setPrefersReducedMotion(event.matches);
    };

    // Add event listener
    // Use deprecated addListener for older browsers
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
  }, []);

  return prefersReducedMotion;
}

/**
 * Get animation configuration based on motion preference
 * @param prefersReducedMotion - Motion preference from useReducedMotion hook
 * @returns Object with safe animation values
 *
 * @example
 * const prefersReducedMotion = useReducedMotion();
 * const animationConfig = getMotionConfig(prefersReducedMotion);
 * <motion.div animate={{ opacity: 1 }} transition={animationConfig.transition} />
 */
export function getMotionConfig(prefersReducedMotion: boolean) {
  if (prefersReducedMotion) {
    return {
      transition: { duration: 0.01, ease: 'linear' },
      animate: { opacity: 1 },
      exit: { opacity: 1 },
      // Disable complex animations
      scale: 1,
      y: 0,
      x: 0,
    };
  }

  return {
    // Use default values when motion is allowed
    transition: undefined,
    animate: undefined,
    exit: undefined,
    scale: undefined,
    y: undefined,
    x: undefined,
  };
}

/**
 * Conditionally apply animation variants based on motion preference
 * @param prefersReducedMotion - Motion preference
 * @param variants - Animation variants to apply
 * @returns Safe variants or null if motion is reduced
 *
 * @example
 * const prefersReducedMotion = useReducedMotion();
 * <motion.div variants={safeVariants(prefersReducedMotion, slideUpVariants)} />
 */
export function safeVariants<T>(
  prefersReducedMotion: boolean,
  variants: T
): T | { animate: { opacity: number } } {
  if (prefersReducedMotion) {
    return {
      animate: { opacity: 1 },
    };
  }
  return variants;
}

/**
 * Get safe animation duration
 * @param prefersReducedMotion - Motion preference
 * @param duration - Desired duration in ms
 * @returns Safe duration (0 if reduced motion, original otherwise)
 */
export function safeDuration(
  prefersReducedMotion: boolean,
  duration: number
): number {
  return prefersReducedMotion ? 0 : duration;
}
