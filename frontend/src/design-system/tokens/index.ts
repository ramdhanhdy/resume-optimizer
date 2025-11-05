/**
 * Design System - Token Index
 *
 * Central export point for all design tokens.
 * Import design tokens from this file to ensure consistency.
 *
 * @example
 * import { colors, spacing, typography } from '@/design-system/tokens';
 */

// Export all token modules
export * from './colors';
export * from './typography';
export * from './spacing';
export * from './shadows';
export * from './borders';
export * from './animations';

// Re-export organized token objects
export { colors } from './colors';
export { typography } from './typography';
export { spacingTokens as spacing } from './spacing';
export { shadowTokens as shadows } from './shadows';
export { borderTokens as borders } from './borders';
export { animationTokens as animations } from './animations';

// Create a comprehensive design tokens object
import { colors } from './colors';
import { typography } from './typography';
import { spacingTokens } from './spacing';
import { shadowTokens } from './shadows';
import { borderTokens } from './borders';
import { animationTokens } from './animations';

export const designTokens = {
  colors,
  typography,
  spacing: spacingTokens,
  shadows: shadowTokens,
  borders: borderTokens,
  animations: animationTokens,
} as const;

// Type export for the complete design system
export type DesignTokens = typeof designTokens;
