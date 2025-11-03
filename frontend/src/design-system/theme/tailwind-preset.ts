/**
 * Design System - Tailwind Preset
 *
 * Extends Tailwind CSS with design system tokens.
 * Import this preset in tailwind.config.js to use design tokens in utility classes.
 */

import type { Config } from 'tailwindcss';
import { colors } from '../tokens/colors';
import { typography } from '../tokens/typography';
import { spacingTokens } from '../tokens/spacing';
import { shadowTokens } from '../tokens/shadows';
import { borderTokens } from '../tokens/borders';
import { animationTokens } from '../tokens/animations';

/**
 * Design system Tailwind preset
 * Extends Tailwind with custom tokens
 */
export const designSystemPreset: Partial<Config> = {
  theme: {
    extend: {
      // Colors
      colors: {
        // Brand colors
        primary: {
          DEFAULT: colors.brand.primary.DEFAULT,
          light: colors.brand.primary.light,
          dark: colors.brand.primary.dark,
        },
        accent: {
          DEFAULT: colors.brand.accent.DEFAULT,
          light: colors.brand.accent.light,
          dark: colors.brand.accent.dark,
        },

        // Neutral colors
        neutral: colors.neutral,

        // Semantic colors
        success: {
          DEFAULT: colors.semantic.success.DEFAULT,
          light: colors.semantic.success.light,
          dark: colors.semantic.success.dark,
        },
        warning: {
          DEFAULT: colors.semantic.warning.DEFAULT,
          light: colors.semantic.warning.light,
          dark: colors.semantic.warning.dark,
        },
        error: {
          DEFAULT: colors.semantic.error.DEFAULT,
          light: colors.semantic.error.light,
          dark: colors.semantic.error.dark,
        },
        info: {
          DEFAULT: colors.semantic.info.DEFAULT,
          light: colors.semantic.info.light,
          dark: colors.semantic.info.dark,
        },

        // Legacy color names (for backward compatibility)
        'soft-neutral': colors.neutral[200],
        'dark-neutral': colors.neutral[400],
        'text-main': colors.neutral[900],
        'background-main': colors.neutral[50],
        'surface-light': colors.background.surface,
        'surface-dark': colors.neutral[100],
        'border-subtle': colors.border.DEFAULT,
      },

      // Font Families
      fontFamily: {
        sans: typography.fontFamilies.sans.split(',').map(f => f.trim()),
        mono: typography.fontFamilies.mono.split(',').map(f => f.trim()),
        display: typography.fontFamilies.display.split(',').map(f => f.trim()),
      },

      // Font Sizes (fluid typography with clamp)
      fontSize: {
        xs: typography.fontSizes.xs,
        sm: typography.fontSizes.sm,
        base: typography.fontSizes.base,
        lg: typography.fontSizes.lg,
        xl: typography.fontSizes.xl,
        '2xl': typography.fontSizes['2xl'],
        '3xl': typography.fontSizes['3xl'],
        '4xl': typography.fontSizes['4xl'],
      },

      // Font Weights
      fontWeight: {
        light: typography.fontWeights.light,
        normal: typography.fontWeights.normal,
        medium: typography.fontWeights.medium,
        semibold: typography.fontWeights.semibold,
        bold: typography.fontWeights.bold,
        extrabold: typography.fontWeights.extrabold,
      },

      // Line Heights
      lineHeight: {
        none: typography.lineHeights.none,
        tight: typography.lineHeights.tight,
        snug: typography.lineHeights.snug,
        normal: typography.lineHeights.normal,
        relaxed: typography.lineHeights.relaxed,
        loose: typography.lineHeights.loose,
      },

      // Letter Spacing
      letterSpacing: {
        tighter: typography.letterSpacing.tighter,
        tight: typography.letterSpacing.tight,
        normal: typography.letterSpacing.normal,
        wide: typography.letterSpacing.wide,
        wider: typography.letterSpacing.wider,
        widest: typography.letterSpacing.widest,
      },

      // Spacing
      spacing: spacingTokens.spacing,

      // Container Max Widths
      maxWidth: spacingTokens.containerWidths,

      // Z-index
      zIndex: spacingTokens.zIndex,

      // Box Shadows
      boxShadow: {
        ...shadowTokens.shadows,
        // Add semantic names
        card: shadowTokens.semantic.card,
        'card-hover': shadowTokens.semantic.cardHover,
        button: shadowTokens.semantic.button,
        'button-hover': shadowTokens.semantic.buttonHover,
        dropdown: shadowTokens.semantic.dropdown,
        modal: shadowTokens.semantic.modal,
        popover: shadowTokens.semantic.popover,
        tooltip: shadowTokens.semantic.tooltip,
      },

      // Drop Shadow (for filters)
      dropShadow: shadowTokens.dropShadowFilters,

      // Border Radius
      borderRadius: {
        ...borderTokens.borderRadius,
        // Add semantic names
        button: borderTokens.semantic.button,
        'button-sm': borderTokens.semantic.buttonSmall,
        'button-lg': borderTokens.semantic.buttonLarge,
        card: borderTokens.semantic.card,
        badge: borderTokens.semantic.badge,
        chip: borderTokens.semantic.chip,
        dialog: borderTokens.semantic.dialog,
      },

      // Border Width
      borderWidth: borderTokens.borderWidth,

      // Animation Durations
      transitionDuration: {
        instant: `${animationTokens.durations.instant}ms`,
        fast: `${animationTokens.durations.fast}ms`,
        base: `${animationTokens.durations.base}ms`,
        slow: `${animationTokens.durations.slow}ms`,
        slower: `${animationTokens.durations.slower}ms`,
        slowest: `${animationTokens.durations.slowest}ms`,
      },

      // Animation Timing Functions
      transitionTimingFunction: {
        ...animationTokens.easings,
        swift: animationTokens.easings.swift,
      },

      // Animation Delays
      transitionDelay: {
        none: `${animationTokens.delays.none}ms`,
        short: `${animationTokens.delays.short}ms`,
        base: `${animationTokens.delays.base}ms`,
        long: `${animationTokens.delays.long}ms`,
        longer: `${animationTokens.delays.longer}ms`,
      },

      // Keyframe Animations
      keyframes: {
        'pulse-slow': {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0.8' },
        },
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { transform: 'translateY(20px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        scaleIn: {
          '0%': { transform: 'scale(0.95)', opacity: '0' },
          '100%': { transform: 'scale(1)', opacity: '1' },
        },
        spin: {
          '0%': { transform: 'rotate(0deg)' },
          '100%': { transform: 'rotate(360deg)' },
        },
        shimmer: {
          '0%': { backgroundPosition: '-1000px 0' },
          '100%': { backgroundPosition: '1000px 0' },
        },
      },

      // Animations
      animation: {
        'pulse-slow': animationTokens.keyframes.pulseSlow.css,
        'fade-in': `fadeIn ${animationTokens.durations.base}ms ${animationTokens.easings.easeOut}`,
        'slide-up': `slideUp ${animationTokens.durations.base}ms ${animationTokens.easings.swiftOut}`,
        'scale-in': `scaleIn ${animationTokens.durations.fast}ms ${animationTokens.easings.swiftOut}`,
        spin: 'spin 1s linear infinite',
        shimmer: 'shimmer 2s linear infinite',
      },
    },
  },
};

export default designSystemPreset;
