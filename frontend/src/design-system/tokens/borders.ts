/**
 * Design System - Border Tokens
 *
 * Centralized border styles including radius, widths, and styles.
 */

// Border Radius - Consistent rounding
export const borderRadius = {
  none: '0',
  xs: '0.125rem',   // 2px
  sm: '0.25rem',    // 4px
  base: '0.375rem', // 6px
  md: '0.5rem',     // 8px (existing radius)
  lg: '0.625rem',   // 10px (shadcn default)
  xl: '0.75rem',    // 12px
  '2xl': '1rem',    // 16px
  '3xl': '1.5rem',  // 24px
  full: '9999px',   // Fully rounded (pills, circles)
} as const;

// Border Widths
export const borderWidth = {
  0: '0',
  1: '1px',
  2: '2px',
  4: '4px',
  8: '8px',
  DEFAULT: '1px',
} as const;

// Border Styles
export const borderStyle = {
  solid: 'solid',
  dashed: 'dashed',
  dotted: 'dotted',
  double: 'double',
  none: 'none',
} as const;

// Semantic border radius - Named radius for specific components
export const semanticRadius = {
  button: borderRadius.md,      // 8px
  buttonSmall: borderRadius.sm, // 4px
  buttonLarge: borderRadius.lg, // 10px
  input: borderRadius.md,       // 8px
  card: borderRadius.lg,        // 10px
  badge: borderRadius.full,     // Fully rounded
  chip: borderRadius.full,      // Fully rounded
  dialog: borderRadius.xl,      // 12px
  popover: borderRadius.lg,     // 10px
  tooltip: borderRadius.base,   // 6px
  avatar: borderRadius.full,    // Circle
  image: borderRadius.md,       // 8px
} as const;

// Outline styles (for focus states)
export const outlineStyles = {
  none: {
    width: '0',
    style: 'none',
    offset: '0',
  },
  default: {
    width: borderWidth[2],
    style: borderStyle.solid,
    offset: '2px',
    color: '#0274BD', // primary color
  },
  focus: {
    width: borderWidth[2],
    style: borderStyle.solid,
    offset: '2px',
    color: '#0274BD', // primary color
  },
  error: {
    width: borderWidth[2],
    style: borderStyle.solid,
    offset: '2px',
    color: '#EF4444', // error color
  },
} as const;

// Divider styles (horizontal and vertical separators)
export const dividers = {
  thin: {
    width: borderWidth[1],
    style: borderStyle.solid,
    color: '#E5E5E5', // border-subtle
  },
  medium: {
    width: borderWidth[2],
    style: borderStyle.solid,
    color: '#C4AD9D', // dark-neutral
  },
  dashed: {
    width: borderWidth[1],
    style: borderStyle.dashed,
    color: '#E5E5E5', // border-subtle
  },
} as const;

// Export all borders as a single object
export const borderTokens = {
  borderRadius,
  borderWidth,
  borderStyle,
  semantic: semanticRadius,
  outlineStyles,
  dividers,
} as const;

// Type exports
export type BorderRadius = typeof borderRadius;
export type BorderWidth = typeof borderWidth;
export type BorderStyle = typeof borderStyle;
export type BorderTokens = typeof borderTokens;
