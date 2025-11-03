/**
 * useKeyboardNavigation Hook
 *
 * React hooks for keyboard navigation and shortcuts.
 * Provides accessible keyboard interaction patterns.
 */

import { useEffect, useCallback, useRef, RefObject } from 'react';

/**
 * Keyboard key codes for common keys
 */
export const Keys = {
  Enter: 'Enter',
  Space: ' ',
  Escape: 'Escape',
  ArrowUp: 'ArrowUp',
  ArrowDown: 'ArrowDown',
  ArrowLeft: 'ArrowLeft',
  ArrowRight: 'ArrowRight',
  Tab: 'Tab',
  Home: 'Home',
  End: 'End',
  PageUp: 'PageUp',
  PageDown: 'PageDown',
} as const;

export type KeyCode = (typeof Keys)[keyof typeof Keys];

/**
 * Hook to listen for specific keyboard shortcuts
 * @param key - Key to listen for
 * @param callback - Callback to execute
 * @param options - Options for the listener
 *
 * @example
 * useKeyPress('Escape', () => closeModal());
 */
export function useKeyPress(
  key: KeyCode | KeyCode[],
  callback: (event: KeyboardEvent) => void,
  options?: {
    /** Require Ctrl/Cmd modifier */
    ctrl?: boolean;
    /** Require Shift modifier */
    shift?: boolean;
    /** Require Alt/Option modifier */
    alt?: boolean;
    /** Prevent default behavior */
    preventDefault?: boolean;
    /** Element to attach listener to (default: document) */
    target?: RefObject<HTMLElement>;
  }
) {
  const { ctrl, shift, alt, preventDefault, target } = options || {};

  useEffect(() => {
    const element = target?.current || document;

    const handleKeyPress = (event: KeyboardEvent) => {
      const keys = Array.isArray(key) ? key : [key];
      const isTargetKey = keys.includes(event.key as KeyCode);

      // Check modifiers
      const ctrlMatch = ctrl ? event.ctrlKey || event.metaKey : true;
      const shiftMatch = shift ? event.shiftKey : true;
      const altMatch = alt ? event.altKey : true;

      if (isTargetKey && ctrlMatch && shiftMatch && altMatch) {
        if (preventDefault) {
          event.preventDefault();
        }
        callback(event);
      }
    };

    element.addEventListener('keydown', handleKeyPress as any);

    return () => {
      element.removeEventListener('keydown', handleKeyPress as any);
    };
  }, [key, callback, ctrl, shift, alt, preventDefault, target]);
}

/**
 * Hook for Escape key handler
 * Common pattern for closing modals/dialogs
 */
export function useEscapeKey(callback: () => void) {
  useKeyPress(Keys.Escape, callback);
}

/**
 * Hook for Enter key handler
 */
export function useEnterKey(callback: () => void, options?: { preventDefault?: boolean }) {
  useKeyPress(Keys.Enter, callback, options);
}

/**
 * Hook for arrow key navigation
 * @param onUp - Callback for Up arrow
 * @param onDown - Callback for Down arrow
 * @param onLeft - Callback for Left arrow
 * @param onRight - Callback for Right arrow
 */
export function useArrowKeys(
  onUp?: () => void,
  onDown?: () => void,
  onLeft?: () => void,
  onRight?: () => void
) {
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      switch (event.key) {
        case Keys.ArrowUp:
          event.preventDefault();
          onUp?.();
          break;
        case Keys.ArrowDown:
          event.preventDefault();
          onDown?.();
          break;
        case Keys.ArrowLeft:
          event.preventDefault();
          onLeft?.();
          break;
        case Keys.ArrowRight:
          event.preventDefault();
          onRight?.();
          break;
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [onUp, onDown, onLeft, onRight]);
}

/**
 * Hook for focus trap (for modals, dialogs)
 * Traps Tab key navigation within a container
 */
export function useFocusTrap(
  containerRef: RefObject<HTMLElement>,
  isActive: boolean
) {
  useEffect(() => {
    if (!isActive || !containerRef.current) return;

    const container = containerRef.current;
    const focusableElements = container.querySelectorAll<HTMLElement>(
      'a[href], button:not([disabled]), textarea:not([disabled]), input:not([disabled]), select:not([disabled]), [tabindex]:not([tabindex="-1"])'
    );

    const firstElement = focusableElements[0];
    const lastElement = focusableElements[focusableElements.length - 1];

    // Focus first element on mount
    firstElement?.focus();

    const handleTab = (event: KeyboardEvent) => {
      if (event.key !== 'Tab') return;

      if (event.shiftKey) {
        // Shift + Tab: move backwards
        if (document.activeElement === firstElement) {
          event.preventDefault();
          lastElement?.focus();
        }
      } else {
        // Tab: move forwards
        if (document.activeElement === lastElement) {
          event.preventDefault();
          firstElement?.focus();
        }
      }
    };

    container.addEventListener('keydown', handleTab as any);

    return () => {
      container.removeEventListener('keydown', handleTab as any);
    };
  }, [containerRef, isActive]);
}

/**
 * Hook to manage focus restoration
 * Stores the currently focused element and restores it later
 */
export function useFocusRestore() {
  const previousFocusRef = useRef<HTMLElement | null>(null);

  const saveFocus = useCallback(() => {
    previousFocusRef.current = document.activeElement as HTMLElement;
  }, []);

  const restoreFocus = useCallback(() => {
    previousFocusRef.current?.focus();
    previousFocusRef.current = null;
  }, []);

  return { saveFocus, restoreFocus };
}

/**
 * Hook for keyboard shortcuts with hints
 * Returns whether the shortcut is pressed and provides a hint string
 */
export function useKeyboardShortcut(
  key: KeyCode,
  callback: () => void,
  options?: {
    ctrl?: boolean;
    shift?: boolean;
    alt?: boolean;
  }
): { hint: string } {
  const { ctrl, shift, alt } = options || {};

  useKeyPress(key, callback, { ...options, preventDefault: true });

  // Build hint string (e.g., "Ctrl+Shift+K")
  const modifiers: string[] = [];
  if (ctrl) modifiers.push(navigator.platform.includes('Mac') ? '⌘' : 'Ctrl');
  if (shift) modifiers.push('Shift');
  if (alt) modifiers.push(navigator.platform.includes('Mac') ? '⌥' : 'Alt');

  const hint = [...modifiers, key].join('+');

  return { hint };
}

/**
 * Hook for list navigation (commonly used in dropdowns, select)
 * @param itemCount - Number of items in the list
 * @param onSelect - Callback when an item is selected
 */
export function useListNavigation(
  itemCount: number,
  onSelect: (index: number) => void
) {
  const [selectedIndex, setSelectedIndex] = useState(-1);

  const handleKeyDown = useCallback(
    (event: KeyboardEvent) => {
      switch (event.key) {
        case Keys.ArrowDown:
          event.preventDefault();
          setSelectedIndex((prev) => (prev + 1) % itemCount);
          break;
        case Keys.ArrowUp:
          event.preventDefault();
          setSelectedIndex((prev) => (prev - 1 + itemCount) % itemCount);
          break;
        case Keys.Home:
          event.preventDefault();
          setSelectedIndex(0);
          break;
        case Keys.End:
          event.preventDefault();
          setSelectedIndex(itemCount - 1);
          break;
        case Keys.Enter:
        case Keys.Space:
          event.preventDefault();
          if (selectedIndex >= 0) {
            onSelect(selectedIndex);
          }
          break;
      }
    },
    [itemCount, selectedIndex, onSelect]
  );

  useEffect(() => {
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [handleKeyDown]);

  return { selectedIndex, setSelectedIndex };
}

// Fix: Import useState
import { useState } from 'react';
