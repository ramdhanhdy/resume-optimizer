/**
 * Design System - Brand Configuration
 *
 * White-label configuration system for customizing the application's brand identity.
 * Supports environment variables for multi-tenant deployments.
 */

import { brandColors, semanticColors } from '../tokens/colors';
import { fontFamilies } from '../tokens/typography';

/**
 * Brand configuration interface
 * Defines all customizable brand properties
 */
export interface BrandConfig {
  /** Brand name displayed in the UI */
  name: string;

  /** Logo URL or path */
  logo: string;

  /** Favicon URL or path */
  favicon: string;

  /** Brand colors override */
  colors: {
    /** Primary brand color (hex) */
    primary: string;
    /** Primary color light variant (hex) */
    primaryLight: string;
    /** Primary color dark variant (hex) */
    primaryDark: string;
    /** Accent/secondary color (hex) */
    accent: string;
    /** Accent color light variant (hex) */
    accentLight: string;
    /** Accent color dark variant (hex) */
    accentDark: string;
  };

  /** Typography overrides */
  typography: {
    /** Primary font family */
    fontFamily: string;
    /** Display/heading font family */
    fontFamilyDisplay?: string;
    /** Monospace font family */
    fontFamilyMono?: string;
  };

  /** Theme customization */
  theme: {
    /** Border radius scale (0-1, where 1 = full rounded) */
    radiusScale?: number;
  };

  /** SEO and metadata */
  metadata: {
    /** Site title */
    title: string;
    /** Meta description */
    description: string;
    /** Keywords */
    keywords: string[];
  };
}

/**
 * Default brand configuration
 * Uses the design token defaults
 */
export const defaultBrandConfig: BrandConfig = {
  name: 'AI Resume Optimizer',
  logo: '/logo.svg',
  favicon: '/favicon.ico',

  colors: {
    primary: brandColors.primary.DEFAULT,
    primaryLight: brandColors.primary.light,
    primaryDark: brandColors.primary.dark,
    accent: brandColors.accent.DEFAULT,
    accentLight: brandColors.accent.light,
    accentDark: brandColors.accent.dark,
  },

  typography: {
    fontFamily: fontFamilies.sans,
    fontFamilyDisplay: fontFamilies.display,
    fontFamilyMono: fontFamilies.mono,
  },

  theme: {
    radiusScale: 1, // Full radius scale (8px base)
  },

  metadata: {
    title: 'AI Resume Optimizer - Optimize Your Resume for Any Job',
    description: 'Use AI to optimize your resume for specific job postings. Get better matches and land more interviews.',
    keywords: ['resume', 'optimizer', 'AI', 'job', 'career', 'ATS'],
  },
};

/**
 * Get brand configuration from environment variables
 * Falls back to defaults if not set
 */
export function getBrandConfig(): BrandConfig {
  return {
    name: import.meta.env.VITE_BRAND_NAME || defaultBrandConfig.name,
    logo: import.meta.env.VITE_BRAND_LOGO || defaultBrandConfig.logo,
    favicon: import.meta.env.VITE_BRAND_FAVICON || defaultBrandConfig.favicon,

    colors: {
      primary: import.meta.env.VITE_PRIMARY_COLOR || defaultBrandConfig.colors.primary,
      primaryLight: import.meta.env.VITE_PRIMARY_COLOR_LIGHT || defaultBrandConfig.colors.primaryLight,
      primaryDark: import.meta.env.VITE_PRIMARY_COLOR_DARK || defaultBrandConfig.colors.primaryDark,
      accent: import.meta.env.VITE_ACCENT_COLOR || defaultBrandConfig.colors.accent,
      accentLight: import.meta.env.VITE_ACCENT_COLOR_LIGHT || defaultBrandConfig.colors.accentLight,
      accentDark: import.meta.env.VITE_ACCENT_COLOR_DARK || defaultBrandConfig.colors.accentDark,
    },

    typography: {
      fontFamily: import.meta.env.VITE_FONT_FAMILY || defaultBrandConfig.typography.fontFamily,
      fontFamilyDisplay: import.meta.env.VITE_FONT_FAMILY_DISPLAY || defaultBrandConfig.typography.fontFamilyDisplay,
      fontFamilyMono: import.meta.env.VITE_FONT_FAMILY_MONO || defaultBrandConfig.typography.fontFamilyMono,
    },

    theme: {
      radiusScale: import.meta.env.VITE_RADIUS_SCALE
        ? parseFloat(import.meta.env.VITE_RADIUS_SCALE)
        : defaultBrandConfig.theme.radiusScale,
    },

    metadata: {
      title: import.meta.env.VITE_META_TITLE || defaultBrandConfig.metadata.title,
      description: import.meta.env.VITE_META_DESCRIPTION || defaultBrandConfig.metadata.description,
      keywords: import.meta.env.VITE_META_KEYWORDS
        ? import.meta.env.VITE_META_KEYWORDS.split(',').map((k: string) => k.trim())
        : defaultBrandConfig.metadata.keywords,
    },
  };
}

/**
 * Convert hex color to HSL format for CSS variables
 * @param hex Hex color string (e.g., "#0274BD")
 * @returns HSL string (e.g., "199 97% 37%")
 */
export function hexToHSL(hex: string): string {
  // Remove # if present
  hex = hex.replace(/^#/, '');

  // Parse hex to RGB
  const r = parseInt(hex.substring(0, 2), 16) / 255;
  const g = parseInt(hex.substring(2, 4), 16) / 255;
  const b = parseInt(hex.substring(4, 6), 16) / 255;

  // Find min and max values
  const max = Math.max(r, g, b);
  const min = Math.min(r, g, b);
  const diff = max - min;

  // Calculate lightness
  const l = (max + min) / 2;

  // Calculate saturation
  let s = 0;
  if (diff !== 0) {
    s = l > 0.5 ? diff / (2 - max - min) : diff / (max + min);
  }

  // Calculate hue
  let h = 0;
  if (diff !== 0) {
    switch (max) {
      case r:
        h = ((g - b) / diff + (g < b ? 6 : 0)) / 6;
        break;
      case g:
        h = ((b - r) / diff + 2) / 6;
        break;
      case b:
        h = ((r - g) / diff + 4) / 6;
        break;
    }
  }

  // Convert to degrees and percentages
  const hDeg = Math.round(h * 360);
  const sPercent = Math.round(s * 100);
  const lPercent = Math.round(l * 100);

  return `${hDeg} ${sPercent}% ${lPercent}%`;
}

/**
 * Apply brand configuration to CSS variables
 * Call this function on app initialization
 */
export function applyBrandConfig(config: BrandConfig): void {
  // Early return for non-browser environments (SSR, tests, Node)
  if (typeof document === 'undefined') {
    return;
  }

  const root = document.documentElement;

  // Apply color variables
  root.style.setProperty('--color-primary', config.colors.primary);
  root.style.setProperty('--primary', hexToHSL(config.colors.primary));
  root.style.setProperty('--accent', hexToHSL(config.colors.accent));

  // Apply typography
  root.style.setProperty('--font-sans', config.typography.fontFamily);
  if (config.typography.fontFamilyDisplay) {
    root.style.setProperty('--font-display', config.typography.fontFamilyDisplay);
  }
  if (config.typography.fontFamilyMono) {
    root.style.setProperty('--font-mono', config.typography.fontFamilyMono);
  }

  // Apply theme scale
  if (config.theme.radiusScale !== undefined) {
    const baseRadius = 8 * config.theme.radiusScale; // 8px is the base
    root.style.setProperty('--radius-lg', `${baseRadius}px`);
    root.style.setProperty('--radius', `${(baseRadius * 0.625) / 16}rem`); // shadcn radius (convert px to rem)
  }

  // Update document title and meta tags
  document.title = config.metadata.title;
  updateMetaTag('description', config.metadata.description);
  updateMetaTag('keywords', config.metadata.keywords.join(', '));

  // Update favicon
  updateFavicon(config.favicon);
}

/**
 * Update meta tag content
 */
function updateMetaTag(name: string, content: string): void {
  if (typeof document === 'undefined') {
    return;
  }

  let meta = document.querySelector(`meta[name="${name}"]`);
  if (!meta) {
    meta = document.createElement('meta');
    meta.setAttribute('name', name);
    document.head.appendChild(meta);
  }
  meta.setAttribute('content', content);
}

/**
 * Update favicon
 */
function updateFavicon(href: string): void {
  if (typeof document === 'undefined') {
    return;
  }

  let link = document.querySelector<HTMLLinkElement>("link[rel~='icon']");
  if (!link) {
    link = document.createElement('link');
    link.rel = 'icon';
    document.head.appendChild(link);
  }
  link.href = href;
}

// Get the current brand configuration
export const brandConfig = getBrandConfig();
