# Responsive Design

Guidelines for composing layouts that adapt smoothly across breakpoints within the AI Resume Optimizer UI.

## Breakpoints
- Tailwind breakpoints align with the brand spec: `sm` 640px, `md` 768px, `lg` 1024px, `xl` 1280px.
- Start with mobile-first defaults and progressively enhance with breakpoint utilities.
- Utilize CSS variables for spacing and typography to maintain proportional scaling.

## Implementation Tips
- Use responsive hooks such as `useIsMobile` for behavioral differences rather than CSS hacks.
- Test components in Storybook-like playgrounds or Vite previews at multiple viewport widths.
- Avoid hardcoded pixel values when tokens are available (e.g., spacing scale).

## TODO
- [ ] Add layout recipes for key product surfaces (wizard, dashboards, modals).
- [ ] Document preferred responsive grid patterns and stack ordering.
- [ ] Include screenshots or GIFs demonstrating responsive transitions.
