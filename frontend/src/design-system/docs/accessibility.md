# Accessibility Guide

Reference checklist for meeting the team’s WCAG 2.1 AA accessibility goals across the design system.

## Principles
- Maintain semantic HTML structure and meaningful ARIA labels.
- Ensure focus is never trapped unintentionally; leverage `useFocusTrap` and `useFocusRestore`.
- Respect reduced motion preferences through the animation hooks.

## Testing Checklist
- Verify keyboard-only navigation for primary flows.
- Confirm focus outlines remain visible against all brand themes.
- Audit color contrast using tokens and automated tooling prior to release.

## TODO
- [ ] Expand with component-level accessibility notes.
- [ ] Provide guidance for screen reader announcements during streaming steps.
- [ ] Document recommended testing workflows (e.g., axe DevTools, Playwright a11y scans).
