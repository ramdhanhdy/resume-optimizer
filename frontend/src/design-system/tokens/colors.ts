/**
 * Design System - Color Tokens
 *
 * Centralized color system for brand consistency and easy customization.
 * All colors use both hex and HSL formats for compatibility with shadcn/ui.
 */

// Brand Colors - Primary identity colors
export const brandColors = {
  primary: {
    DEFAULT: '#0274BD',
    light: '#3A9AD9',
    dark: '#015A96',
    hsl: '199 97% 37%', // For shadcn components
  },
  accent: {
    DEFAULT: '#F57251',
    light: '#FF8A6B',
    dark: '#DC5A3C',
    hsl: '14 100% 64%', // For shadcn components
  },
} as const;

// Neutral Colors - Grayscale palette
export const neutralColors = {
  50: '#FAFAF9',   // Background main
  100: '#F5F5F5',  // Surface dark
  200: '#E9E6DD',  // Soft neutral
  300: '#E5E5E5',  // Border subtle
  400: '#C4AD9D',  // Dark neutral
  500: '#9CA3AF',  // Mid gray
  600: '#6B7280',  // Text secondary
  700: '#4B5563',  // Text tertiary
  800: '#374151',  // Text strong
  900: '#1c1c1e',  // Text main
} as const;

// Semantic Colors - Contextual meanings
export const semanticColors = {
  success: {
    DEFAULT: '#10B981',
    light: '#34D399',
    dark: '#059669',
    hsl: '160 84% 39%',
  },
  warning: {
    DEFAULT: '#FF9500',
    light: '#FBB040',
    dark: '#E08600',
    hsl: '36 100% 50%',
  },
  error: {
    DEFAULT: '#EF4444',
    light: '#F87171',
    dark: '#DC2626',
    hsl: '0 84% 60%',
  },
  info: {
    DEFAULT: '#0274BD',
    light: '#3A9AD9',
    dark: '#015A96',
    hsl: '199 97% 37%',
  },
} as const;

// Text Colors - Typography color variants
export const textColors = {
  primary: neutralColors[900],      // Main text
  secondary: neutralColors[600],    // Secondary text
  tertiary: neutralColors[500],     // Muted text
  disabled: neutralColors[400],     // Disabled state
  inverse: '#FFFFFF',               // Text on dark backgrounds
  link: brandColors.primary.DEFAULT,
  linkHover: brandColors.primary.dark,
} as const;

// Background Colors - Surface and container backgrounds
export const backgroundColors = {
  main: neutralColors[50],          // #FAFAF9
  surface: '#FFFFFF',               // Card/panel backgrounds
  surfaceHover: neutralColors[100], // Hover state
  elevated: '#FFFFFF',              // Elevated surfaces (modals, popovers)
  overlay: 'rgba(0, 0, 0, 0.5)',   // Modal overlays
  disabled: neutralColors[200],     // Disabled backgrounds
} as const;

// Border Colors - Strokes and dividers
export const borderColors = {
  DEFAULT: neutralColors[300],      // #E5E5E5
  subtle: '#F0F0F0',                // Very subtle borders
  medium: neutralColors[400],       // More prominent borders
  strong: neutralColors[600],       // Strong emphasis
  focus: brandColors.primary.DEFAULT, // Focus state
  error: semanticColors.error.DEFAULT,
} as const;

// Status Colors - For badges, chips, and status indicators
export const statusColors = {
  new: {
    bg: '#DBEAFE',
    text: '#1E40AF',
    border: '#93C5FD',
  },
  inProgress: {
    bg: '#FEF3C7',
    text: '#92400E',
    border: '#FCD34D',
  },
  completed: {
    bg: '#D1FAE5',
    text: '#065F46',
    border: '#6EE7B7',
  },
  failed: {
    bg: '#FEE2E2',
    text: '#991B1B',
    border: '#FCA5A5',
  },
} as const;

// Chart Colors - For data visualization
export const chartColors = {
  1: brandColors.primary.DEFAULT,
  2: brandColors.accent.DEFAULT,
  3: semanticColors.success.DEFAULT,
  4: semanticColors.warning.DEFAULT,
  5: semanticColors.info.DEFAULT,
} as const;

// Export all colors as a single object
export const colors = {
  brand: brandColors,
  neutral: neutralColors,
  semantic: semanticColors,
  text: textColors,
  background: backgroundColors,
  border: borderColors,
  status: statusColors,
  chart: chartColors,
} as const;

// Type exports for TypeScript
export type BrandColors = typeof brandColors;
export type NeutralColors = typeof neutralColors;
export type SemanticColors = typeof semanticColors;
export type Colors = typeof colors;
