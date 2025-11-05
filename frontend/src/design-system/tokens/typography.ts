/**
 * Design System - Typography Tokens
 *
 * Centralized typography system with font families, sizes, weights, and line heights.
 * Uses clamp() for fluid typography that scales responsively.
 */

// Font Families
export const fontFamilies = {
  sans: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif, "Apple Color Emoji", "Segoe UI Emoji", "Segoe UI Symbol"',
  mono: '"SF Mono", "Consolas", "Monaco", "Courier New", monospace',
  display: 'system-ui, -apple-system, sans-serif', // For headings
} as const;

// Font Sizes - Using clamp() for fluid, responsive typography
// Format: clamp(min, preferred, max)
export const fontSizes = {
  xs: 'clamp(0.75rem, 0.7rem + 0.25vw, 0.875rem)',      // 12px → 14px
  sm: 'clamp(0.875rem, 0.825rem + 0.25vw, 1rem)',       // 14px → 16px
  base: 'clamp(1rem, 0.95rem + 0.25vw, 1.125rem)',      // 16px → 18px
  lg: 'clamp(1.125rem, 1.05rem + 0.375vw, 1.25rem)',    // 18px → 20px
  xl: 'clamp(1.25rem, 1.15rem + 0.5vw, 1.5rem)',        // 20px → 24px
  '2xl': 'clamp(1.5rem, 1.35rem + 0.75vw, 2rem)',       // 24px → 32px
  '3xl': 'clamp(2rem, 1.75rem + 1.25vw, 3rem)',         // 32px → 48px
  '4xl': 'clamp(2.5rem, 2.15rem + 1.75vw, 3.75rem)',    // 40px → 60px
} as const;

// Font Sizes - Static values for precise control (when fluid sizing isn't needed)
export const fontSizesStatic = {
  xs: '0.75rem',    // 12px
  sm: '0.875rem',   // 14px
  base: '1rem',     // 16px
  lg: '1.125rem',   // 18px
  xl: '1.25rem',    // 20px
  '2xl': '1.5rem',  // 24px
  '3xl': '2rem',    // 32px
  '4xl': '2.5rem',  // 40px
} as const;

// Font Weights
export const fontWeights = {
  light: 300,
  normal: 400,
  medium: 500,
  semibold: 600,
  bold: 700,
  extrabold: 800,
} as const;

// Line Heights
export const lineHeights = {
  none: 1,
  tight: 1.2,
  snug: 1.375,
  normal: 1.5,
  relaxed: 1.75,
  loose: 2,
} as const;

// Letter Spacing
export const letterSpacing = {
  tighter: '-0.05em',
  tight: '-0.025em',
  normal: '0',
  wide: '0.025em',
  wider: '0.05em',
  widest: '0.1em',
} as const;

// Typography Presets - Complete text styles for common patterns
export const typographyPresets = {
  // Headings
  h1: {
    fontFamily: fontFamilies.display,
    fontSize: fontSizes['4xl'],
    fontWeight: fontWeights.bold,
    lineHeight: lineHeights.tight,
    letterSpacing: letterSpacing.tight,
  },
  h2: {
    fontFamily: fontFamilies.display,
    fontSize: fontSizes['3xl'],
    fontWeight: fontWeights.bold,
    lineHeight: lineHeights.tight,
    letterSpacing: letterSpacing.tight,
  },
  h3: {
    fontFamily: fontFamilies.display,
    fontSize: fontSizes['2xl'],
    fontWeight: fontWeights.semibold,
    lineHeight: lineHeights.snug,
    letterSpacing: letterSpacing.normal,
  },
  h4: {
    fontFamily: fontFamilies.display,
    fontSize: fontSizes.xl,
    fontWeight: fontWeights.semibold,
    lineHeight: lineHeights.snug,
    letterSpacing: letterSpacing.normal,
  },
  h5: {
    fontFamily: fontFamilies.display,
    fontSize: fontSizes.lg,
    fontWeight: fontWeights.medium,
    lineHeight: lineHeights.normal,
    letterSpacing: letterSpacing.normal,
  },
  h6: {
    fontFamily: fontFamilies.display,
    fontSize: fontSizes.base,
    fontWeight: fontWeights.medium,
    lineHeight: lineHeights.normal,
    letterSpacing: letterSpacing.normal,
  },

  // Body Text
  body: {
    fontFamily: fontFamilies.sans,
    fontSize: fontSizes.base,
    fontWeight: fontWeights.normal,
    lineHeight: lineHeights.normal,
    letterSpacing: letterSpacing.normal,
  },
  bodyLarge: {
    fontFamily: fontFamilies.sans,
    fontSize: fontSizes.lg,
    fontWeight: fontWeights.normal,
    lineHeight: lineHeights.relaxed,
    letterSpacing: letterSpacing.normal,
  },
  bodySmall: {
    fontFamily: fontFamilies.sans,
    fontSize: fontSizes.sm,
    fontWeight: fontWeights.normal,
    lineHeight: lineHeights.normal,
    letterSpacing: letterSpacing.normal,
  },

  // UI Elements
  button: {
    fontFamily: fontFamilies.sans,
    fontSize: fontSizes.base,
    fontWeight: fontWeights.medium,
    lineHeight: lineHeights.none,
    letterSpacing: letterSpacing.normal,
  },
  buttonSmall: {
    fontFamily: fontFamilies.sans,
    fontSize: fontSizes.sm,
    fontWeight: fontWeights.medium,
    lineHeight: lineHeights.none,
    letterSpacing: letterSpacing.normal,
  },
  buttonLarge: {
    fontFamily: fontFamilies.sans,
    fontSize: fontSizes.lg,
    fontWeight: fontWeights.medium,
    lineHeight: lineHeights.none,
    letterSpacing: letterSpacing.normal,
  },

  // Labels & Captions
  label: {
    fontFamily: fontFamilies.sans,
    fontSize: fontSizes.sm,
    fontWeight: fontWeights.medium,
    lineHeight: lineHeights.normal,
    letterSpacing: letterSpacing.normal,
  },
  caption: {
    fontFamily: fontFamilies.sans,
    fontSize: fontSizes.xs,
    fontWeight: fontWeights.normal,
    lineHeight: lineHeights.normal,
    letterSpacing: letterSpacing.normal,
  },
  overline: {
    fontFamily: fontFamilies.sans,
    fontSize: fontSizes.xs,
    fontWeight: fontWeights.semibold,
    lineHeight: lineHeights.normal,
    letterSpacing: letterSpacing.wider,
    textTransform: 'uppercase' as const,
  },

  // Code
  code: {
    fontFamily: fontFamilies.mono,
    fontSize: fontSizes.sm,
    fontWeight: fontWeights.normal,
    lineHeight: lineHeights.normal,
    letterSpacing: letterSpacing.normal,
  },
  codeBlock: {
    fontFamily: fontFamilies.mono,
    fontSize: fontSizes.sm,
    fontWeight: fontWeights.normal,
    lineHeight: lineHeights.relaxed,
    letterSpacing: letterSpacing.normal,
  },
} as const;

// Export everything as a single object
export const typography = {
  fontFamilies,
  fontSizes,
  fontSizesStatic,
  fontWeights,
  lineHeights,
  letterSpacing,
  presets: typographyPresets,
} as const;

// Type exports
export type Typography = typeof typography;
export type TypographyPreset = keyof typeof typographyPresets;
