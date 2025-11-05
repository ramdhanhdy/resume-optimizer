# Customization Guide

Instructions for adapting the design system to new brands while preserving shared accessibility guarantees.

## Brand Configuration
- Update `frontend/src/design-system/theme/brand-config.ts` with new brand tokens.
- Configure runtime overrides via `.env` values such as `VITE_PRIMARY_COLOR`.
- Apply themes early in `frontend/src/index.tsx` so downstream components receive updated CSS variables.

## Extensibility Tips
- Keep custom variants additive; avoid modifying shared base components without design review.
- When introducing new tokens, document intent and fallback values for dark mode.
- Validate visual changes in the streaming flow to ensure gradients and states remain legible.

## TODO
- [ ] Provide step-by-step instructions for launching a white-label theme.
- [ ] Surface best practices for mapping brand palettes to HSL token slots.
- [ ] Add guidance for coordinating design token updates with backend branding settings.
