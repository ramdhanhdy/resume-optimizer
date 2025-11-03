/**
 * Design System - Shadow Tokens
 *
 * Elevation system using box shadows for depth and hierarchy.
 * Based on Material Design elevation principles.
 */

// Shadow scale - Progressive elevation
export const shadows = {
  none: 'none',

  // Subtle shadows for cards and panels
  xs: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
  sm: '0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px -1px rgba(0, 0, 0, 0.1)',

  // Base shadow (existing 'subtle' shadow)
  base: '0 1px 3px rgba(0, 0, 0, 0.08)',

  // Medium shadows for dropdowns and popovers
  md: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -2px rgba(0, 0, 0, 0.1)',
  lg: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -4px rgba(0, 0, 0, 0.1)',

  // Large shadows for modals and elevated content
  xl: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.1)',
  '2xl': '0 25px 50px -12px rgba(0, 0, 0, 0.25)',

  // Special shadows
  inner: 'inset 0 2px 4px 0 rgba(0, 0, 0, 0.05)',
  outline: '0 0 0 3px rgba(2, 116, 189, 0.5)', // Focus outline

  // Colored shadows for emphasis
  primaryGlow: '0 0 20px rgba(2, 116, 189, 0.3)',
  accentGlow: '0 0 20px rgba(245, 114, 81, 0.3)',
  successGlow: '0 0 20px rgba(16, 185, 129, 0.3)',
  errorGlow: '0 0 20px rgba(239, 68, 68, 0.3)',
} as const;

// Semantic shadows - Named shadows for specific use cases
export const semanticShadows = {
  card: shadows.sm,
  cardHover: shadows.md,
  button: shadows.xs,
  buttonHover: shadows.sm,
  dropdown: shadows.lg,
  modal: shadows['2xl'],
  popover: shadows.md,
  tooltip: shadows.sm,
  floating: shadows.xl,
  focusRing: shadows.outline,
} as const;

// Elevation levels (Material Design inspired)
export const elevation = {
  0: shadows.none,       // Flat, no elevation
  1: shadows.xs,         // Slightly raised
  2: shadows.sm,         // Cards, panels
  3: shadows.md,         // Raised cards
  4: shadows.lg,         // Dropdowns, popovers
  6: shadows.xl,         // Floating action buttons
  8: shadows['2xl'],     // Modals, dialogs
} as const;

// Drop shadow filters (for SVG and images)
export const dropShadowFilters = {
  sm: 'drop-shadow(0 1px 2px rgba(0, 0, 0, 0.05))',
  base: 'drop-shadow(0 1px 3px rgba(0, 0, 0, 0.1))',
  md: 'drop-shadow(0 4px 6px rgba(0, 0, 0, 0.1))',
  lg: 'drop-shadow(0 10px 15px rgba(0, 0, 0, 0.1))',
  xl: 'drop-shadow(0 20px 25px rgba(0, 0, 0, 0.15))',
} as const;

// Export all shadows as a single object
export const shadowTokens = {
  shadows,
  semantic: semanticShadows,
  elevation,
  dropShadowFilters,
} as const;

// Type exports
export type Shadows = typeof shadows;
export type SemanticShadows = typeof semanticShadows;
export type ShadowTokens = typeof shadowTokens;
