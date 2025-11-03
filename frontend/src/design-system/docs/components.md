# Components Guide

High-level reference for the shadcn/ui components curated for the AI Resume Optimizer frontend.

## Overview
- Components live in `frontend/src/components/ui` and follow the design system tokens.
- Prefer composition over heavy abstraction to keep variants predictable.
- Each component exports TypeScript props with strict typing to align with the design tokens.

## Usage Notes
- Import components via aliased paths (for example, `@/components/ui/button`).
- Leverage provided `variant` and `size` props instead of custom class names where possible.
- Pair interactive components with the hooks in `frontend/src/hooks` for keyboard support.

## TODO
- [ ] Document component-specific props and patterns.
- [ ] Add code samples that demonstrate multi-agent workflow screens.
- [ ] Capture common accessibility pitfalls for each component.
