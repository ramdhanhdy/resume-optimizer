# Design System Documentation

## Overview

Welcome to the AI Resume Optimizer Design System. This comprehensive design system provides a scalable, modular framework for building consistent, accessible, and responsive user interfaces.

## Architecture

### Core Systems

1. **Design Tokens** (`tokens/`)
   - Colors, typography, spacing, shadows, borders, animations
   - Centralized source of truth for all design decisions
   - TypeScript-typed for autocompletion

2. **Theme System** (`theme/`)
   - Brand customization and white-labeling
   - Environment-based configuration
   - CSS variable integration

3. **Component Library** (`components/ui/`)
   - shadcn/ui components (2025 latest)
   - Custom specialized components
   - Fully accessible and responsive

4. **Animation System** (`animations/`)
   - Framer Motion variants and transitions
   - prefers-reduced-motion support
   - Consistent motion design

5. **Form System** (`forms/`)
   - React Hook Form + Zod validation
   - Accessible field wrappers
   - Pre-built schemas

6. **Hooks** (`hooks/`)
   - Responsive utilities (useMediaQuery)
   - Keyboard navigation (useKeyboardNavigation)
   - Accessibility helpers

## Quick Start

### Using Design Tokens

```typescript
import { colors, typography, spacing } from '@/design-system/tokens';

// Use in components
const MyComponent = () => (
  <div style={{
    color: colors.brand.primary.DEFAULT,
    fontSize: typography.fontSizes.lg,
    padding: spacing.spacing[4],
  }}>
    Hello World
  </div>
);
```

### Using shadcn Components

```typescript
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';

const MyFeature = () => (
  <Card>
    <Button variant="default">Click Me</Button>
  </Card>
);
```

### Using Animations

```typescript
import { motion } from 'framer-motion';
import { slideUpVariants, useReducedMotion } from '@/design-system/animations';

const AnimatedComponent = () => {
  const prefersReducedMotion = useReducedMotion();

  return (
    <motion.div
      variants={prefersReducedMotion ? undefined : slideUpVariants}
      initial="initial"
      animate="animate"
    >
      Content
    </motion.div>
  );
};
```

### Using Form Validation

```typescript
import { useFormValidation } from '@/design-system/forms';
import { jobPostingSchema } from '@/design-system/forms';

const MyForm = () => {
  const form = useFormValidation(jobPostingSchema, {
    defaultValues: { jobPosting: '' },
  });

  const onSubmit = form.handleSubmit((data) => {
    console.log('Valid data:', data);
  });

  return <form onSubmit={onSubmit}>...</form>;
};
```

## Documentation

- **[Components Guide](./components.md)** - Component API documentation
- **[Accessibility Guide](./accessibility.md)** - WCAG 2.1 AA compliance checklist
- **[Responsive Design](./responsive.md)** - Breakpoints and mobile-first patterns
- **[Customization Guide](./customization.md)** - Brand configuration and theming

## File Structure

```
design-system/
├── tokens/              # Design tokens
│   ├── colors.ts
│   ├── typography.ts
│   ├── spacing.ts
│   ├── shadows.ts
│   ├── borders.ts
│   ├── animations.ts
│   └── index.ts
├── theme/               # Theme system
│   ├── brand-config.ts
│   ├── tailwind-preset.ts
│   └── css-variables.css
├── animations/          # Motion system
│   ├── variants.ts
│   ├── transitions.ts
│   ├── use-reduced-motion.ts
│   └── index.ts
├── forms/               # Form system
│   ├── schemas/
│   ├── use-form-validation.ts
│   ├── field-wrapper.tsx
│   └── index.ts
└── docs/                # Documentation
    ├── README.md
    ├── components.md
    ├── accessibility.md
    ├── responsive.md
    └── customization.md
```

## Key Features

### ✅ shadcn/ui 2025 Integration
- Latest components with Field API
- CSS variables for theming
- Radix UI primitives for accessibility

### ✅ Design Token System
- 200+ design tokens across 6 categories
- TypeScript types for safety
- Tailwind integration

### ✅ Brand Customization
- Environment variable configuration
- White-labeling support
- Multi-tenant ready

### ✅ Accessibility (WCAG 2.1 AA)
- ARIA attributes throughout
- Keyboard navigation patterns
- Screen reader support
- Focus management

### ✅ Responsive Design
- Mobile-first breakpoints
- Fluid typography with clamp()
- Touch-friendly interfaces (44px targets)

### ✅ Animation System
- prefers-reduced-motion support
- Framer Motion variants library
- Performance-optimized

### ✅ Form Validation
- React Hook Form integration
- Zod schemas
- Accessible error handling

## Contributing

When adding new components or features:

1. Follow existing patterns and conventions
2. Add TypeScript types for all exports
3. Include accessibility attributes
4. Test responsive behavior
5. Document your changes

## Support

For questions or issues with the design system, please refer to the detailed documentation files or reach out to the development team.

---

**Version**: 1.0.0
**Last Updated**: 2025
**Built with**: React 19, Tailwind CSS v4, shadcn/ui, Framer Motion
