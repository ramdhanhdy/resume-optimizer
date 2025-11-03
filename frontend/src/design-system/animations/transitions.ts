/**
 * Design System - Transition Configurations
 *
 * Reusable transition configurations for Framer Motion.
 */

import type { Transition } from 'framer-motion';
import { animationTokens } from '../tokens/animations';

/**
 * Fast transition (150ms)
 * Use for: Hover states, tooltips, quick feedback
 */
export const fastTransition: Transition = {
  duration: animationTokens.durations.fast / 1000,
  ease: [0.4, 0.0, 0.2, 1], // Swift easing
};

/**
 * Base transition (300ms)
 * Use for: Most animations, default choice
 */
export const baseTransition: Transition = {
  duration: animationTokens.durations.base / 1000,
  ease: [0.4, 0.0, 0.2, 1], // Swift easing
};

/**
 * Slow transition (500ms)
 * Use for: Complex animations, screen transitions
 */
export const slowTransition: Transition = {
  duration: animationTokens.durations.slow / 1000,
  ease: [0.4, 0.0, 0.2, 1], // Swift easing
};

/**
 * Bounce transition
 * Use for: Playful interactions, success states
 */
export const bounceTransition: Transition = {
  duration: animationTokens.durations.slow / 1000,
  ease: [0.68, -0.55, 0.265, 1.55], // Bounce easing
};

/**
 * Spring transition
 * Use for: Natural, physics-based motion
 */
export const springTransition: Transition = {
  type: 'spring',
  stiffness: 300,
  damping: 30,
};

/**
 * Smooth spring transition
 * Use for: Smooth, natural animations
 */
export const smoothSpringTransition: Transition = {
  type: 'spring',
  stiffness: 200,
  damping: 20,
};

/**
 * Stiff spring transition
 * Use for: Quick, snappy animations
 */
export const stiffSpringTransition: Transition = {
  type: 'spring',
  stiffness: 400,
  damping: 40,
};

/**
 * Ease out transition
 * Use for: Elements entering the screen
 */
export const easeOutTransition: Transition = {
  duration: animationTokens.durations.base / 1000,
  ease: [0.0, 0.0, 0.2, 1], // Decelerate
};

/**
 * Ease in transition
 * Use for: Elements exiting the screen
 */
export const easeInTransition: Transition = {
  duration: animationTokens.durations.base / 1000,
  ease: [0.4, 0.0, 1, 1], // Accelerate
};

/**
 * Stagger configuration
 * For animating lists and groups
 */
export const staggerConfig = {
  fast: {
    staggerChildren: animationTokens.stagger.fast / 1000,
  },
  base: {
    staggerChildren: animationTokens.stagger.base / 1000,
    delayChildren: animationTokens.delays.short / 1000,
  },
  slow: {
    staggerChildren: animationTokens.stagger.slow / 1000,
    delayChildren: animationTokens.delays.base / 1000,
  },
} as const;

/**
 * Layout transition
 * For layout animations (position, size changes)
 */
export const layoutTransition: Transition = {
  type: 'spring',
  stiffness: 500,
  damping: 50,
};

/**
 * No transition (instant)
 * Use for: Reduced motion preference or immediate changes
 */
export const instantTransition: Transition = {
  duration: 0,
  ease: 'linear',
};

// Export all transitions as a collection
export const transitions = {
  fast: fastTransition,
  base: baseTransition,
  slow: slowTransition,
  bounce: bounceTransition,
  spring: springTransition,
  smoothSpring: smoothSpringTransition,
  stiffSpring: stiffSpringTransition,
  easeOut: easeOutTransition,
  easeIn: easeInTransition,
  layout: layoutTransition,
  instant: instantTransition,
  stagger: staggerConfig,
} as const;

export type TransitionName = keyof typeof transitions;
