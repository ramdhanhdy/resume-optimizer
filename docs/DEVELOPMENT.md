# Development Guide

This guide covers development workflows, code quality tools, and best practices for contributing to the AI Resume Optimizer project.

## Table of Contents

- [Development Guide](#development-guide)
  - [Running Locally](#running-locally)
  - [Backend Development](#backend-development)
  - [Frontend Development](#frontend-development)
  - [Code Quality](#code-quality)
  - [Testing](#testing)
  - [Design System](#design-system)
  - [Continuous Integration](#continuous-integration)

## Running Locally

### Quick Start (Both Services)

The easiest way to run both backend and frontend simultaneously:

**Windows:**
```bash
.\start.bat
```

**macOS/Linux:**
```bash
bash ./start.sh
```

These scripts will:
1. Start the backend server on port 8000
2. Start the frontend dev server on port 5173
3. Open the application in your default browser

### Individual Services

**Backend:**
```bash
cd backend
python server.py
```

**Alternative (with hot reload for development):**
```bash
cd backend
uvicorn server:app --reload --host 0.0.0.0 --port 8000
```

**Frontend:**
```bash
cd frontend
npm run dev
```

**Preview production build:**
```bash
cd frontend
npm run build
npm run preview
```

**Access points:**
- Frontend: http://localhost:5173 (Vite default)
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs (Swagger UI)

## Backend Development

### Project Structure

```
backend/
├── src/
│   ├── agents/           # AI agent implementations
│   ├── api/              # Multi-provider LLM clients
│   ├── app/              # FastAPI application
│   ├── database/         # SQLite database layer
│   ├── middleware/       # Error handling middleware
│   ├── routes/           # API route definitions
│   ├── services/         # Core business logic
│   ├── streaming/        # SSE streaming infrastructure
│   ├── templates/        # HTML templates for exports
│   └── utils/            # Utility functions
├── prompts/              # Agent prompt files
├── .env.example          # Environment template
├── server.py             # Application entry point
└── Procfile              # Cloud Run process definition
```

### Key Development Patterns

**Agent Development:**
- All agents inherit from `BaseAgent` in `src/agents/base.py`
- Implement `run()` method for agent logic
- Use `yield` for streaming output chunks
- Return structured data with validation

**Streaming Events:**
- Emit events via `StreamManager.emit()`
- Use predefined event types in `src/streaming/events.py`
- Include metadata for cost tracking and monitoring

**Database Operations:**
- Use `db.py` for database connections
- Implement migrations in `database/migrations/`
- Follow existing schema patterns for new tables

### Environment Configuration

Copy `.env.example` to `.env` and configure:

```bash
# Required (minimum one provider)
OPENROUTER_API_KEY=your_openrouter_key_here
# or
GEMINI_API_KEY=your_gemini_key_here

# Optional providers
CEREBRAS_API_KEY=your_cerebras_key_here
EXA_API_KEY=your_exa_key_here
ZENMUX_API_KEY=your_zenmux_key_here
LONGCAT_API_KEY=your_longcat_key_here

# Per-agent model configuration
ANALYZER_MODEL=gemini::gemini-2.5-pro
OPTIMIZER_MODEL=openrouter::openai/gpt-5.1
IMPLEMENTER_MODEL=openrouter::anthropic/claude-sonnet-4.5
VALIDATOR_MODEL=gemini::gemini-2.5-pro
POLISH_MODEL=openrouter::anthropic/claude-sonnet-4.5

# Database
DATABASE_PATH=./data/applications.db

# CORS
CORS_ORIGINS=*  # Restrict in production

# Rate limiting
MAX_FREE_RUNS=5
```

**Testing API endpoints:**
```bash
# Health check
curl http://localhost:8000/api/health

# Test agent pipeline
curl -X POST http://localhost:8000/api/analyze-job \
  -H "Content-Type: application/json" \
  -d '{"job_posting_text": "Senior Software Engineer", "resume": "Your resume text"}'
```

## Frontend Development

### Project Structure

```
frontend/
├── src/
│   ├── components/           # React components
│   │   ├── shared/           # Shared UI components
│   │   ├── tabs/             # Tabbed interface
│   │   ├── ui/               # shadcn/ui components
│   │   └── *.tsx             # Main page components
│   ├── design-system/        # Design tokens and theme
│   │   ├── animations/       # Framer Motion variants
│   │   ├── docs/             # Design system docs
│   │   ├── forms/            # Form validation
│   │   ├── theme/            # Brand configuration
│   │   └── tokens/           # 200+ design tokens
│   ├── hooks/                # Custom React hooks
│   ├── lib/                  # Utilities
│   ├── services/             # API and storage
│   │   ├── api.ts            # SSE client
│   │   └── storage/          # IndexedDB/LocalStorage adapters
│   ├── types/                # TypeScript types
│   ├── utils/                # Helper functions
│   ├── App.tsx               # Root component
│   ├── index.css             # Global styles (CSS variables)
│   └── index.tsx             # Entry point
├── .env.example              # Environment template
├── components.json           # shadcn/ui config
├── DESIGN_SYSTEM.md          # Design system guide
└── vite.config.ts            # Vite configuration
```

### Key Development Patterns

**State Management:**
- Use `LocalStorageAdapter` for persistent state
- Use `IndexedDBAdapter` for large data storage
- Use `StateManager` for reactive state updates
- Implement proper cleanup in `useEffect` hooks

**API Communication:**
- Use `api.ts` for all backend communication
- Handle SSE reconnection and replay
- Implement proper error boundaries

**Component Structure:**
- Use functional components with hooks
- Implement proper TypeScript interfaces
- Follow the existing component patterns in `src/components/`

### Environment Configuration

Copy `.env.example` to `.env.local`:

```bash
# Backend API URL
VITE_API_URL=http://localhost:8000

# Optional branding
# VITE_BRAND_NAME=Resume Optimizer
# VITE_PRIMARY_COLOR=#0274BD
# VITE_ACCENT_COLOR=#F57251
```

**Testing UI components:**
```bash
# Start dev server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

## Code Quality

### Backend (Python)

**Formatting:**
```bash
cd backend

# Format code with black
black .

# Check with black (no changes)
black --check .

# Lint with ruff
ruff check .

# Auto-fix linting issues
ruff check . --fix
```

**Requirements:**
- Install `black` and `ruff` in your virtual environment
- Run before committing changes
- CI will enforce these checks

### Frontend (TypeScript/React)

**Linting:**
```bash
cd frontend

# Lint code (ESLint)
npm run lint

# Lint with auto-fix
npm run lint -- --fix
```

**Type Checking:**
```bash
# Type check without compilation
npx tsc --noEmit
```

**Requirements:**
- ESLint configured in `package.json`
- TypeScript strict mode enabled
- Run before committing changes

## Testing

### Backend Unit Tests

```bash
cd backend

# Run all tests
python -m pytest

# Run with verbose output
python -m pytest -v

# Run specific test file
python -m pytest tests/test_agents.py

# Run with coverage
python -m pytest --cov=src --cov-report=html
```

**Test structure:**
```
backend/tests/
├── __init__.py
├── test_agents.py
├── test_api.py
├── test_streaming.py
└── test_utils.py
```

### Frontend Tests

**TODO:** Frontend testing is planned but not yet implemented.

**Recommended setup:**
```bash
# Install testing dependencies
npm install --save-dev vitest @testing-library/react @testing-library/jest-dom

# Add test scripts to package.json
{
  "scripts": {
    "test": "vitest",
    "test:ui": "vitest --ui"
  }
}
```

**When implemented, tests will cover:**
- Component rendering
- User interactions
- API integration
- State management
- Accessibility features

## Design System

The frontend uses a comprehensive design system built on **shadcn/ui (2025)**.

### Key Features

- **200+ Design Tokens**: Colors, typography, spacing, shadows, borders, animations
- **shadcn Components**: 10+ accessible, customizable components (Button, Card, Badge, Dialog, Input, Tabs, Tooltip)
- **WCAG 2.1 AA Compliance**: Built-in accessibility features including keyboard navigation and reduced motion
- **Responsive Design**: Mobile-first with breakpoint hooks (`useIsMobile`, `useBreakpoint`)
- **Motion System**: 20+ Framer Motion variants with `useReducedMotion` hook
- **Brand Customization**: White-labeling via CSS variables and environment variables
- **Form Validation**: React Hook Form + Zod integration

### Color System

**CSS Variables** define the single source of truth:
```css
/* frontend/src/index.css */
:root {
  --primary: 199 97% 42%;  /* #0274BD */
  --accent: 14 88% 63%;    /* #F57251 */
  /* ... additional colors ... */
}
```

**Usage in components:**
```tsx
// ✅ Correct - uses CSS variables
<div className="bg-primary text-accent">

// ❌ Incorrect - hardcoded colors
<div className="bg-[#0274BD] text-[#F57251]">
```

### Component Usage

```tsx
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

// Use design tokens for custom styling
import { colors, typography } from '@/design-system/tokens';

// Animations with accessibility
import { slideUpVariants, useReducedMotion } from '@/design-system/animations';

const prefersReducedMotion = useReducedMotion();
<motion.div 
  variants={prefersReducedMotion ? undefined : slideUpVariants}
  initial="initial"
  animate="animate"
>
  Content
</motion.div>
```

### Brand Customization

**Runtime theming via environment variables:**
```bash
# In .env.local (Vercel Project Settings for production)
VITE_BRAND_NAME="My Resume Tool"
VITE_PRIMARY_COLOR="#FF5722"
VITE_ACCENT_COLOR="#4CAF50"
```

**Function call in app initialization:**
```tsx
// frontend/src/index.tsx
import { applyBrandConfig } from '@/design-system/theme/brand-config';

applyBrandConfig(); // Called on app startup
```

### Accessibility Guidelines

- **Keyboard Navigation**: All interactive elements must be keyboard accessible
- **Focus Management**: Use `useFocusTrap` for modals and dialogs
- **ARIA Attributes**: Add labels, roles, and live regions
- **Reduced Motion**: Respect `prefers-reduced-motion` with `useReducedMotion` hook
- **Color Contrast**: Minimum 4.5:1 ratio for text
- **Screen Readers**: Semantic HTML and proper heading hierarchy

### Documentation

- **Design System Guide**: [`frontend/DESIGN_SYSTEM.md`](./frontend/DESIGN_SYSTEM.md)
- **Component Docs**: [`frontend/src/design-system/docs/README.md`](./frontend/src/design-system/docs/README.md)
- **shadcn/ui Docs**: https://ui.shadcn.com/

## Continuous Integration

**TODO:** GitHub Actions workflow is planned but not yet implemented.

**Recommended CI pipeline:**

```yaml
# .github/workflows/ci.yml (recommended)
name: CI

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: |
          cd backend
          uv pip install -r requirements.txt
          uv pip install black ruff pytest pytest-cov
      - run: cd backend && black --check .
      - run: cd backend && ruff check .
      - run: cd backend && python -m pytest --cov=src

  frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '20'
      - run: cd frontend && npm ci
      - run: cd frontend && npm run lint
      - run: cd frontend && npx tsc --noEmit
      - run: cd frontend && npm run build

  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run security audit
        run: |
          cd backend && pip install safety && safety check
          cd ../frontend && npm audit
```

### Pre-commit Hooks

**Recommended setup (optional):**

```bash
# Install pre-commit
pip install pre-commit
pre-commit install

# Add .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.0.0
    hooks:
      - id: black
        language_version: python3.11
  - repo: https://github.com/charliermarsh/ruff-pre-commit
    rev: v0.0.260
    hooks:
      - id: ruff
  - repo: https://github.com/pre-commit/mirrors-eslint
    rev: v8.42.0
    hooks:
      - id: eslint
        files: frontend
        types: [javascript, jsx, ts, tsx]
```

## Further Reading

- [Agent Development Guide](./AGENTS.md) - Complete agent architecture
- [Design System Guide](./frontend/DESIGN_SYSTEM.md) - Frontend design system
- [Setup Guide](./docs/setup/SETUP.md) - Initial setup instructions
- [API Reference](./docs/API_REFERENCE.md) - API documentation
- [Troubleshooting](./docs/TROUBLESHOOTING.md) - Common issues and solutions
