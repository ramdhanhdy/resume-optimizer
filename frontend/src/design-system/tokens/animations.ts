/**
 * Design System - Animation Tokens
 *
 * Centralized animation system with durations, easings, and timing functions.
 * Designed for consistency and performance.
 */

// Animation Durations (in milliseconds)
export const durations = {
  instant: 0,
  fast: 150,
  base: 300,
  slow: 500,
  slower: 700,
  slowest: 1000,
} as const;

// Easing Functions (cubic-bezier timing functions)
export const easings = {
  // Standard easings
  linear: 'linear',
  easeIn: 'cubic-bezier(0.4, 0.0, 1, 1)',
  easeOut: 'cubic-bezier(0.0, 0.0, 0.2, 1)',
  easeInOut: 'cubic-bezier(0.4, 0.0, 0.2, 1)',

  // Custom easings
  swift: 'cubic-bezier(0.4, 0.0, 0.2, 1)',        // Existing swift easing
  swiftOut: 'cubic-bezier(0.0, 0.0, 0.2, 1)',     // Material Design
  swiftIn: 'cubic-bezier(0.4, 0.0, 1, 1)',        // Material Design

  // Spring-like easings
  bounce: 'cubic-bezier(0.68, -0.55, 0.265, 1.55)',
  elastic: 'cubic-bezier(0.68, -0.6, 0.32, 1.6)',

  // Anticipation easings
  anticipate: 'cubic-bezier(0.36, 0, 0.66, -0.56)',

  // Material Design easings
  standard: 'cubic-bezier(0.4, 0.0, 0.2, 1)',
  decelerate: 'cubic-bezier(0.0, 0.0, 0.2, 1)',
  accelerate: 'cubic-bezier(0.4, 0.0, 1, 1)',
} as const;

// Transition Presets - Complete transition definitions
export const transitions = {
  // Fast transitions (hover states, etc.)
  fast: {
    duration: durations.fast,
    easing: easings.swift,
    css: `${durations.fast}ms ${easings.swift}`,
  },

  // Base transitions (default)
  base: {
    duration: durations.base,
    easing: easings.swift,
    css: `${durations.base}ms ${easings.swift}`,
  },

  // Slow transitions (complex animations)
  slow: {
    duration: durations.slow,
    easing: easings.swift,
    css: `${durations.slow}ms ${easings.swift}`,
  },

  // Fade transitions
  fade: {
    duration: durations.base,
    easing: easings.easeOut,
    css: `${durations.base}ms ${easings.easeOut}`,
  },

  // Scale transitions (buttons, modals)
  scale: {
    duration: durations.fast,
    easing: easings.swiftOut,
    css: `${durations.fast}ms ${easings.swiftOut}`,
  },

  // Slide transitions (drawers, panels)
  slide: {
    duration: durations.base,
    easing: easings.standard,
    css: `${durations.base}ms ${easings.standard}`,
  },

  // Bounce transitions (playful interactions)
  bounce: {
    duration: durations.slow,
    easing: easings.bounce,
    css: `${durations.slow}ms ${easings.bounce}`,
  },
} as const;

// Animation Delays
export const delays = {
  none: 0,
  short: 50,
  base: 100,
  long: 200,
  longer: 300,
} as const;

// Stagger timing (for sequential animations)
export const stagger = {
  fast: 50,    // 50ms between items
  base: 100,   // 100ms between items
  slow: 150,   // 150ms between items
} as const;

// Keyframe animations (for CSS animations)
export const keyframes = {
  // Existing pulse-slow animation
  pulseSlow: {
    name: 'pulse-slow',
    duration: '3s',
    timing: easings.easeInOut,
    iterations: 'infinite',
    css: 'pulse-slow 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
  },

  // Fade in animation
  fadeIn: {
    name: 'fadeIn',
    duration: `${durations.base}ms`,
    timing: easings.easeOut,
    iterations: '1',
  },

  // Slide up animation
  slideUp: {
    name: 'slideUp',
    duration: `${durations.base}ms`,
    timing: easings.swiftOut,
    iterations: '1',
  },

  // Scale in animation
  scaleIn: {
    name: 'scaleIn',
    duration: `${durations.fast}ms`,
    timing: easings.swiftOut,
    iterations: '1',
  },

  // Spin animation (for loaders)
  spin: {
    name: 'spin',
    duration: '1s',
    timing: easings.linear,
    iterations: 'infinite',
  },

  // Shimmer animation (for skeletons)
  shimmer: {
    name: 'shimmer',
    duration: '2s',
    timing: easings.linear,
    iterations: 'infinite',
  },
} as const;

// Motion preferences
export const motion = {
  // Will be used to check prefers-reduced-motion
  reduceMotion: false, // Default, will be overridden by hook

  // Safe animation values for reduced motion
  reduced: {
    duration: durations.instant,
    easing: easings.linear,
    css: `0ms linear`,
  },
} as const;

// Export all animations as a single object
export const animationTokens = {
  durations,
  easings,
  transitions,
  delays,
  stagger,
  keyframes,
  motion,
} as const;

// Type exports
export type Durations = typeof durations;
export type Easings = typeof easings;
export type Transitions = typeof transitions;
export type AnimationTokens = typeof animationTokens;
