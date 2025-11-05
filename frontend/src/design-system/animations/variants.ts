/**
 * Design System - Framer Motion Variants
 *
 * Centralized animation variants for consistent motion design.
 * All variants respect prefers-reduced-motion media query.
 */

import type { Variants, Transition } from 'framer-motion';
import { animationTokens } from '../tokens/animations';
import { baseTransition, fastTransition, slowTransition, bounceTransition } from './transitions';

/**
 * Fade In/Out Variants
 */
export const fadeVariants: Variants = {
  initial: {
    opacity: 0,
  },
  animate: {
    opacity: 1,
    transition: fastTransition,
  },
  exit: {
    opacity: 0,
    transition: fastTransition,
  },
};

/**
 * Slide Up Variants
 * Element slides up from below with fade
 */
export const slideUpVariants: Variants = {
  initial: {
    opacity: 0,
    y: 20,
  },
  animate: {
    opacity: 1,
    y: 0,
    transition: baseTransition,
  },
  exit: {
    opacity: 0,
    y: -10,
    transition: fastTransition,
  },
};

/**
 * Slide Down Variants
 * Element slides down from above with fade
 */
export const slideDownVariants: Variants = {
  initial: {
    opacity: 0,
    y: -20,
  },
  animate: {
    opacity: 1,
    y: 0,
    transition: baseTransition,
  },
  exit: {
    opacity: 0,
    y: 10,
    transition: fastTransition,
  },
};

/**
 * Slide Left Variants
 * Element slides in from the right
 */
export const slideLeftVariants: Variants = {
  initial: {
    opacity: 0,
    x: 20,
  },
  animate: {
    opacity: 1,
    x: 0,
    transition: baseTransition,
  },
  exit: {
    opacity: 0,
    x: -20,
    transition: fastTransition,
  },
};

/**
 * Slide Right Variants
 * Element slides in from the left
 */
export const slideRightVariants: Variants = {
  initial: {
    opacity: 0,
    x: -20,
  },
  animate: {
    opacity: 1,
    x: 0,
    transition: baseTransition,
  },
  exit: {
    opacity: 0,
    x: 20,
    transition: fastTransition,
  },
};

/**
 * Scale In Variants
 * Element scales up from smaller size
 */
export const scaleVariants: Variants = {
  initial: {
    opacity: 0,
    scale: 0.95,
  },
  animate: {
    opacity: 1,
    scale: 1,
    transition: fastTransition,
  },
  exit: {
    opacity: 0,
    scale: 0.95,
    transition: fastTransition,
  },
};

/**
 * Pop In Variants
 * Element pops in with bounce effect
 */
export const popVariants: Variants = {
  initial: {
    opacity: 0,
    scale: 0.8,
  },
  animate: {
    opacity: 1,
    scale: 1,
    transition: bounceTransition,
  },
  exit: {
    opacity: 0,
    scale: 0.9,
    transition: fastTransition,
  },
};

/**
 * Stagger Children Variants
 * Parent container that staggers its children
 */
export const staggerContainerVariants: Variants = {
  initial: {},
  animate: {
    transition: {
      staggerChildren: animationTokens.stagger.base / 1000,
      delayChildren: animationTokens.delays.short / 1000,
    },
  },
  exit: {
    transition: {
      staggerChildren: animationTokens.stagger.fast / 1000,
      staggerDirection: -1,
    },
  },
};

/**
 * Stagger Fast - Quicker stagger timing
 */
export const staggerFastContainerVariants: Variants = {
  initial: {},
  animate: {
    transition: {
      staggerChildren: animationTokens.stagger.fast / 1000,
    },
  },
};

/**
 * Stagger Slow - Slower stagger timing
 */
export const staggerSlowContainerVariants: Variants = {
  initial: {},
  animate: {
    transition: {
      staggerChildren: animationTokens.stagger.slow / 1000,
      delayChildren: animationTokens.delays.base / 1000,
    },
  },
};

/**
 * Collapse/Expand Variants
 * For accordion-style animations
 */
export const collapseVariants: Variants = {
  collapsed: {
    height: 0,
    opacity: 0,
    overflow: 'hidden',
    transition: baseTransition,
  },
  expanded: {
    height: 'auto',
    opacity: 1,
    overflow: 'visible',
    transition: baseTransition,
  },
};

/**
 * Drawer Variants - Slide from edges
 */
export const drawerVariants = {
  // From left
  left: {
    initial: { x: '-100%' },
    animate: { x: 0, transition: baseTransition },
    exit: { x: '-100%', transition: baseTransition },
  },
  // From right
  right: {
    initial: { x: '100%' },
    animate: { x: 0, transition: baseTransition },
    exit: { x: '100%', transition: baseTransition },
  },
  // From top
  top: {
    initial: { y: '-100%' },
    animate: { y: 0, transition: baseTransition },
    exit: { y: '-100%', transition: baseTransition },
  },
  // From bottom
  bottom: {
    initial: { y: '100%' },
    animate: { y: 0, transition: baseTransition },
    exit: { y: '100%', transition: baseTransition },
  },
} as const;

/**
 * Modal/Dialog Variants
 * Backdrop + Content animations
 */
export const modalBackdropVariants: Variants = {
  initial: {
    opacity: 0,
  },
  animate: {
    opacity: 1,
    transition: fastTransition,
  },
  exit: {
    opacity: 0,
    transition: fastTransition,
  },
};

export const modalContentVariants: Variants = {
  initial: {
    opacity: 0,
    scale: 0.95,
    y: 20,
  },
  animate: {
    opacity: 1,
    scale: 1,
    y: 0,
    transition: baseTransition,
  },
  exit: {
    opacity: 0,
    scale: 0.95,
    y: 20,
    transition: fastTransition,
  },
};

/**
 * List Item Variants
 * For use with stagger container
 */
export const listItemVariants: Variants = {
  initial: {
    opacity: 0,
    x: -10,
  },
  animate: {
    opacity: 1,
    x: 0,
    transition: fastTransition,
  },
  exit: {
    opacity: 0,
    x: 10,
    transition: fastTransition,
  },
};

/**
 * Notification/Toast Variants
 */
export const notificationVariants: Variants = {
  initial: {
    opacity: 0,
    y: -10,
    scale: 0.95,
  },
  animate: {
    opacity: 1,
    y: 0,
    scale: 1,
    transition: baseTransition,
  },
  exit: {
    opacity: 0,
    scale: 0.95,
    transition: fastTransition,
  },
};

/**
 * Hover Variants - For interactive elements
 */
export const hoverVariants = {
  scale: {
    scale: 1.05,
    transition: { duration: 0.2 },
  },
  lift: {
    y: -2,
    transition: { duration: 0.2 },
  },
  glow: {
    boxShadow: '0 0 20px rgba(2, 116, 189, 0.3)',
    transition: { duration: 0.2 },
  },
} as const;

/**
 * Tap Variants - For button press feedback
 */
export const tapVariants = {
  scale: {
    scale: 0.95,
  },
  shrink: {
    scale: 0.98,
  },
} as const;

/**
 * Loading Spinner Variants
 */
export const spinnerVariants: Variants = {
  animate: {
    rotate: 360,
    transition: {
      duration: 1,
      repeat: Infinity,
      ease: 'linear',
    },
  },
};

/**
 * Pulse Variants - For attention-grabbing effects
 */
export const pulseVariants: Variants = {
  animate: {
    scale: [1, 1.05, 1],
    opacity: [1, 0.8, 1],
    transition: {
      duration: 2,
      repeat: Infinity,
      ease: 'easeInOut',
    },
  },
};

// Export all variants as a collection
export const motionVariants = {
  fade: fadeVariants,
  slideUp: slideUpVariants,
  slideDown: slideDownVariants,
  slideLeft: slideLeftVariants,
  slideRight: slideRightVariants,
  scale: scaleVariants,
  pop: popVariants,
  staggerContainer: staggerContainerVariants,
  staggerFast: staggerFastContainerVariants,
  staggerSlow: staggerSlowContainerVariants,
  collapse: collapseVariants,
  drawer: drawerVariants,
  modalBackdrop: modalBackdropVariants,
  modalContent: modalContentVariants,
  listItem: listItemVariants,
  notification: notificationVariants,
  hover: hoverVariants,
  tap: tapVariants,
  spinner: spinnerVariants,
  pulse: pulseVariants,
} as const;

export type MotionVariantName = keyof typeof motionVariants;
