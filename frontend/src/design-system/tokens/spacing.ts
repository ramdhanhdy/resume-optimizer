/**
 * Design System - Spacing Tokens
 *
 * Centralized spacing scale based on 4px base unit.
 * Provides consistent spacing for margins, padding, gaps, and layout.
 */

// Base spacing scale (4px base unit)
export const spacing = {
  0: '0',
  0.5: '0.125rem',  // 2px
  1: '0.25rem',     // 4px
  1.5: '0.375rem',  // 6px
  2: '0.5rem',      // 8px
  2.5: '0.625rem',  // 10px
  3: '0.75rem',     // 12px
  3.5: '0.875rem',  // 14px
  4: '1rem',        // 16px
  5: '1.25rem',     // 20px
  6: '1.5rem',      // 24px
  7: '1.75rem',     // 28px
  8: '2rem',        // 32px
  9: '2.25rem',     // 36px
  10: '2.5rem',     // 40px
  11: '2.75rem',    // 44px - Minimum touch target
  12: '3rem',       // 48px
  14: '3.5rem',     // 56px
  16: '4rem',       // 64px
  20: '5rem',       // 80px
  24: '6rem',       // 96px
  28: '7rem',       // 112px
  32: '8rem',       // 128px
  36: '9rem',       // 144px
  40: '10rem',      // 160px
  44: '11rem',      // 176px
  48: '12rem',      // 192px
  52: '13rem',      // 208px
  56: '14rem',      // 224px
  60: '15rem',      // 240px
  64: '16rem',      // 256px
  72: '18rem',      // 288px
  80: '20rem',      // 320px
  96: '24rem',      // 384px
} as const;

// Semantic spacing - Named spacing for specific use cases
export const semanticSpacing = {
  // Component spacing
  componentPaddingXs: spacing[2],   // 8px
  componentPaddingSm: spacing[3],   // 12px
  componentPaddingMd: spacing[4],   // 16px
  componentPaddingLg: spacing[6],   // 24px
  componentPaddingXl: spacing[8],   // 32px

  // Section spacing
  sectionGapXs: spacing[4],         // 16px
  sectionGapSm: spacing[6],         // 24px
  sectionGapMd: spacing[8],         // 32px
  sectionGapLg: spacing[12],        // 48px
  sectionGapXl: spacing[16],        // 64px

  // Stack spacing (vertical rhythm)
  stackXs: spacing[1],              // 4px
  stackSm: spacing[2],              // 8px
  stackMd: spacing[4],              // 16px
  stackLg: spacing[6],              // 24px
  stackXl: spacing[8],              // 32px

  // Inline spacing (horizontal)
  inlineXs: spacing[1],             // 4px
  inlineSm: spacing[2],             // 8px
  inlineMd: spacing[3],             // 12px
  inlineLg: spacing[4],             // 16px
  inlineXl: spacing[6],             // 24px

  // Touch targets (accessibility)
  touchTarget: spacing[11],         // 44px minimum
  touchTargetLarge: spacing[12],    // 48px

  // Page layout
  pageGutterXs: spacing[4],         // 16px (mobile)
  pageGutterSm: spacing[6],         // 24px (tablet)
  pageGutterMd: spacing[8],         // 32px (desktop)
  pageGutterLg: spacing[12],        // 48px (large desktop)
} as const;

// Container max widths for responsive layouts
export const containerWidths = {
  xs: '20rem',      // 320px
  sm: '24rem',      // 384px
  md: '28rem',      // 448px
  lg: '32rem',      // 512px
  xl: '36rem',      // 576px
  '2xl': '42rem',   // 672px
  '3xl': '48rem',   // 768px
  '4xl': '56rem',   // 896px
  '5xl': '64rem',   // 1024px
  '6xl': '72rem',   // 1152px
  '7xl': '80rem',   // 1280px
  full: '100%',
  screen: '100vw',
} as const;

// Breakpoints (for reference, matches Tailwind defaults)
export const breakpoints = {
  sm: '640px',      // Small devices (tablets)
  md: '768px',      // Medium devices (small laptops)
  lg: '1024px',     // Large devices (desktops)
  xl: '1280px',     // Extra large devices (large desktops)
  '2xl': '1536px',  // 2X large devices (ultra-wide)
} as const;

// Z-index scale for layering
export const zIndex = {
  hide: -1,
  base: 0,
  dropdown: 1000,
  sticky: 1020,
  fixed: 1030,
  modalBackdrop: 1040,
  modal: 1050,
  popover: 1060,
  tooltip: 1070,
  notification: 1080,
  top: 9999,
} as const;

// Export all spacing as a single object
export const spacingTokens = {
  spacing,
  semantic: semanticSpacing,
  containerWidths,
  breakpoints,
  zIndex,
} as const;

// Type exports
export type Spacing = typeof spacing;
export type SemanticSpacing = typeof semanticSpacing;
export type SpacingTokens = typeof spacingTokens;
