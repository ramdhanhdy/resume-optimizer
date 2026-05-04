# UI Component Specification

## Overview

This document specifies the UI component architecture and behavior for the Resume Optimizer application, including screen flow, animations, and responsive design requirements.

## Component Architecture

### Screen Flow

The application follows a three-screen flow:

```
InputScreen → ProcessingScreen → RevealScreen
     ↓              ↓              ↓
  Data Input    Processing     Results Display
  & Upload      Animation      & Export
```

### Core Components

#### 1. InputScreen (`frontend/src/components/InputScreen.tsx`)

**Purpose**: Handle resume upload and job posting input

**Key Features**:
- File upload with drag-and-drop support
- Job posting text/URL input
- Auto-advance logic when both inputs are ready
- Real-time validation feedback

**Props Interface**:
```typescript
interface InputScreenProps {
  onStart: (data: {
    resumeText: string;
    jobInput: string;
    isUrl: boolean;
  }) => void;
}
```

**State Management**:
- `resumeText`: Extracted text from uploaded file
- `jobInput`: Raw job posting input (text or URL)
- `isUrl`: Boolean flag for URL detection
- `isReady`: Both inputs valid and ready
- `isLoading`: File processing state

**Validation Rules**:
- Resume text must be > 10 characters after extraction
- Job input must be non-empty
- URL validation for job posting links
- File type validation (PDF, DOCX, TXT)

**Auto-Advance Logic**:
```typescript
useEffect(() => {
  if (isReady && !isLoading && resumeText.trim().length > 0) {
    const timeoutId = setTimeout(handleContinue, 1000);
    return () => clearTimeout(timeoutId);
  }
}, [isReady, isLoading, resumeText]);
```

#### 2. ProcessingScreen (`frontend/src/components/ProcessingScreen.tsx`)

**Purpose**: Display real-time processing progress and insights

**Key Features**:
- Real-time streaming updates (SSE)
- Progress bar with step tracking
- Insights cards display
- Error handling and recovery
- Feature flag for streaming vs. legacy

**Props Interface**:
```typescript
interface ProcessingScreenProps {
  onComplete: (appState: ProcessingResult) => void;
  resumeText: string;
  jobText?: string;
  jobUrl?: string;
}
```

**Processing Steps**:
1. **Analyzing Job** (Agent 1)
2. **Planning Optimizations** (Agent 2)
3. **Writing Resume** (Agent 3)
4. **Validating Changes** (Agent 4)
5. **Polishing Final** (Agent 5)

**Streaming Integration**:
```typescript
const { state, isComplete, isFailed, isConnected } = useProcessingJob(jobId);

// State includes:
// - insights: Real-time insight messages
// - steps: Progress tracking per step
// - metrics: Validation scores and counts
// - currentStep: Active processing step
```

**Animation Specifications**:
- Phase transitions use opacity and transform
- Progress bar smoothly reflects completion percentage
- Insights cards animate in with staggered timing
- Connection status indicator for streaming health

#### 3. RevealScreen (`frontend/src/components/RevealScreen.tsx`)

**Purpose**: Display before/after comparison and export options

**Key Features**:
- Side-by-side resume comparison
- Change highlighting and diff view
- Validation scores display
- Export functionality (DOCX/PDF)
- Application data persistence

**Props Interface**:
```typescript
interface RevealScreenProps {
  applicationData: ApplicationData;
  onExport: (format: 'docx' | 'pdf') => void;
  onBack: () => void;
}
```

**Comparison View**:
- Original resume on left
- Optimized resume on right
- Changes highlighted with color coding
- Scroll synchronization between panels

**Validation Display**:
- Overall score with visual indicator
- Category-specific scores (Keywords, Structure, etc.)
- Improvement recommendations
- Fact-check validation results

#### 4. ExportModal (`frontend/src/components/ExportModal.tsx`)

**Purpose**: Handle resume export in multiple formats

**Export Formats**:
- DOCX with proper formatting
- PDF with layout preservation
- Plain text option

**Features**:
- Format selection interface
- Download progress tracking
- Error handling for export failures
- Preview before download

## Styling Specifications

### Theme System

**Color Palette** (Tailwind v4 CSS custom properties):
```css
@theme {
  --color-primary: #0274BD;        /* Primary actions */
  --color-accent: #F57251;         /* Highlights and warnings */
  --color-background-main: #FAFAF9; /* Main background */
  --color-surface-light: #FFFFFF;  /* Card backgrounds */
  --color-surface-dark: #F5F5F5;   /* Hover states */
  --color-border-subtle: #E5E5E5;  /* Dividers */
  --color-warning: #FF9500;        /* Warning messages */
  --color-text-main: #1c1c1e;      /* Primary text */
}
```

**Typography**:
```css
body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
}
```

**Animations**:
```css
--ease-swift: cubic-bezier(0.4, 0.0, 0.2, 1);
--animate-pulse-slow: pulse-slow 3s cubic-bezier(0.4, 0, 0.6, 1) infinite;
```

### Component Styling

#### Input Screen
- **Layout**: Centered form with max-width constraints
- **Upload Area**: Drag-and-drop zone with hover states
- **Form Elements**: Consistent input styling with focus states
- **Button**: Primary action button with loading states

#### Processing Screen
- **Layout**: Full-screen with fixed positioning for elements
- **Progress Bar**: Animated gradient background
- **Insights Cards**: Fixed height with scroll overflow
- **Status Text**: Large, centered text with fade transitions

#### Reveal Screen
- **Layout**: Two-column comparison with responsive breakpoints
- **Diff Highlighting**: Color-coded changes (additions, deletions, modifications)
- **Export Button**: Floating action button with hover effects

## Animation Specifications

### Page Transitions

```typescript
const pageVariants = {
  initial: { opacity: 0, y: 20 },
  in: { opacity: 1, y: 0 },
  out: { opacity: 0, y: -20 }
};

const pageTransition = {
  type: "tween",
  ease: [0.4, 0.0, 0.2, 1], // --ease-swift
  duration: 0.4
};
```

### Component Animations

#### Input Screen
- **Form Fields**: Fade in on mount with staggered delay
- **Upload Button**: Scale animation on hover
- **Success States**: Checkmark animation with bounce

#### Processing Screen
- **Phase Text**: Cross-fade between phase changes
- **Progress Bar**: Smooth width transitions
- **Insights**: Slide and fade in animation
- **Loading Spinner**: Continuous rotation animation

#### Reveal Screen
- **Comparison Panels**: Slide in from sides
- **Highlight Effects**: Fade in for changes
- **Score Animations**: Count-up animation for scores

### Performance Considerations

- Use `transform` and `opacity` for 60fps animations
- Implement `will-change` sparingly for GPU acceleration
- Avoid layout thrashing during animations
- Use `requestAnimationFrame` for custom animations

## Responsive Design

### Breakpoints

```css
/* Mobile */
@media (max-width: 768px) {
  /* Single column layout */
  /* Touch-friendly targets */
}

/* Tablet */
@media (min-width: 769px) and (max-width: 1024px) {
  /* Adjusted spacing */
  /* Medium-sized components */
}

/* Desktop */
@media (min-width: 1025px) {
  /* Full layout */
  /* Optimal spacing */
}
```

### Mobile Adaptations

#### Input Screen
- Stack form elements vertically
- Increase touch target sizes (44px minimum)
- Simplify upload interface

#### Processing Screen
- Center content vertically
- Reduce insight card count
- Larger progress indicator

#### Reveal Screen
- Switch to tabbed interface
- Single resume view at a time
- Simplified export options

## Accessibility Specifications

### Semantic HTML
- Use proper heading hierarchy (h1, h2, h3)
- Form labels associated with inputs
- Button elements for interactive controls
- ARIA labels for custom components

### Keyboard Navigation
- Tab order follows visual flow
- Focus indicators clearly visible
- Escape key closes modals
- Enter key activates primary actions

### Screen Reader Support
- Progress announcements for processing
- Change descriptions for diff view
- Error messages read aloud
- Form validation feedback

### Color Contrast
- Text contrast ratio: 4.5:1 minimum
- Interactive elements: 3:1 minimum
- Color not used as only indicator

## Error Handling

### Form Validation
```typescript
const [errors, setErrors] = useState<Record<string, string>>({});

const validateForm = () => {
  const newErrors: Record<string, string> = {};
  
  if (!resumeText || resumeText.length < 10) {
    newErrors.resume = "Please upload a valid resume file";
  }
  
  if (!jobInput.trim()) {
    newErrors.job = "Please provide a job posting";
  }
  
  setErrors(newErrors);
  return Object.keys(newErrors).length === 0;
};
```

### Network Errors
- Retry mechanisms with exponential backoff
- User-friendly error messages
- Fallback to offline mode where possible
- Error reporting for debugging

### File Upload Errors
- File size validation (10MB maximum)
- File type validation
- Corrupted file detection
- Upload progress indication

## Performance Requirements

### Load Performance
- Initial bundle size: < 500KB gzipped
- Time to interactive: < 3 seconds
- First contentful paint: < 1.5 seconds

### Runtime Performance
- Animation frame rate: 60fps
- Input response time: < 100ms
- Memory usage: < 50MB

### Optimization Strategies
- Code splitting for route-based chunks
- Lazy loading of heavy components
- Image optimization for resume previews
- Service worker for offline support

## Testing Requirements

### Unit Tests
- Component rendering tests
- State management tests
- Validation logic tests
- Animation behavior tests

### Integration Tests
- Screen flow transitions
- API integration
- File upload handling
- Export functionality

### E2E Tests
- Complete user journey
- Cross-browser compatibility
- Mobile device testing
- Accessibility compliance

## Browser Compatibility

### Supported Browsers
- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

### Required Features
- ES2020 JavaScript support
- CSS Grid and Flexbox
- File API for uploads
- EventSource for streaming

### Polyfills
- `whatwg-fetch` for older browsers
- `core-js` for ES features
- Custom properties fallback

## Security Considerations

### File Upload Security
- File type validation on both client and server
- File size limits enforced
- Malicious file scanning
- Secure temporary storage

### Data Privacy
- No sensitive data in localStorage
- Secure API communication
- Input sanitization
- XSS prevention

## Future Enhancements

### Planned Features
1. **Dark Mode**: Theme switching capability
2. **Advanced Animations**: Micro-interactions and delighters
3. **Progressive Web App**: Offline functionality
4. **Internationalization**: Multi-language support
5. **Advanced Export**: More format options

### Component Library
- Design system documentation
- Reusable component library
- Storybook integration
- Component testing suite

---

**Specification Version**: 1.0  
**Last Updated**: 2025-01-31  
**Status**: Implemented and tested
