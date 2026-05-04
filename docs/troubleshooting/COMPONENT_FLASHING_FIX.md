# Component Flashing/Disappearing Troubleshooting Guide

## Problem Description

Components appear briefly then disappear, causing a "flashing" effect that disrupts the user experience. This issue can occur even when CSS styling appears correct.

## Symptoms

- Components render momentarily then vanish
- Screen transitions appear jumpy or incomplete
- Auto-advance functionality behaves unexpectedly
- Console may show React re-render warnings

## Root Causes

### 1. Invalid Framer Motion Easing Function
- **Issue**: Components use `ease: 'swift'` which is not a valid Framer Motion easing string
- **Impact**: Animations may malfunction, skip, or cause unexpected behavior
- **Detection**: Check browser console for animation warnings

### 2. Auto-Advance Logic Race Condition
- **Issue**: `useEffect` triggers without proper validation in InputScreen
- **Impact**: Auto-advance fires even with invalid/missing data
- **Detection**: Screen advances prematurely before data is ready

### 3. Missing Defensive Checks
- **Issue**: `handleContinue` doesn't validate data before proceeding
- **Impact**: Attempts processing with invalid data
- **Detection**: Downstream errors or empty states

## Diagnostic Steps

1. **Check Browser Console**
   ```javascript
   // Look for animation warnings
   // Check for React strict mode double-renders
   // Verify no JavaScript errors
   ```

2. **Test Auto-Advance Behavior**
   - Upload file without job text → Should not advance
   - Type job text without file → Should not advance
   - Upload invalid file → Should not advance

3. **Verify Animation Settings**
   ```javascript
   // In React DevTools, check component easing props
   // Should be: [0.4, 0.0, 0.2, 1] not 'swift'
   ```

## Resolution Steps

### Step 1: Fix Framer Motion Easing

**Files to modify**: All component files using transitions

**Before**:
```tsx
transition={{ duration: 0.4, ease: 'swift' }}
```

**After**:
```tsx
transition={{ duration: 0.4, ease: [0.4, 0.0, 0.2, 1] }}
```

**Verification**: Build completes without animation warnings

### Step 2: Improve Auto-Advance Logic

**File**: `frontend/src/components/InputScreen.tsx`

**Update useEffect**:
```tsx
useEffect(() => {
  // Only auto-advance if we have BOTH ready state AND valid resume text
  if (isReady && !isLoading && resumeText.trim().length > 0) {
    const timeoutId = setTimeout(handleContinue, 1000);
    return () => clearTimeout(timeoutId);
  }
}, [isReady, isLoading, resumeText]);
```

**Verification**: Auto-advance only works with valid data

### Step 3: Add Defensive Validation

**Update handleContinue**:
```tsx
const handleContinue = () => {
  // Defensive check: don't proceed without valid data
  if (isReady && resumeText && resumeText.trim().length > 10) {
    const isUrl = jobInput.startsWith('http://') || jobInput.startsWith('https://');
    onStart({ resumeText, jobInput, isUrl });
  } else {
    console.warn('Cannot continue: missing resume text or job input');
  }
};
```

**Verification**: Console warnings for invalid attempts

## Advanced Troubleshooting

### If Issues Persist

#### Option A: Disable React.StrictMode (Temporary)
**File**: `frontend/src/index.tsx`
```tsx
// For debugging only - re-enable for production
const root = ReactDOM.createRoot(rootElement);
root.render(<App />);
```

#### Option B: Remove Auto-Advance Entirely
- Remove entire `useEffect` auto-advance logic
- Require manual button click only
- More predictable user experience

### Performance Verification

**Check build output**:
```bash
cd frontend
npm run build
```

**Expected results**:
- CSS size: ~19.73 kB (gzipped: ~4.55 kB)
- JS size: ~331.52 kB (gzipped: ~105.73 kB)
- Build time: < 2 seconds
- No TypeScript errors

## Prevention Measures

1. **Code Review Checklist**
   - [ ] Verify easing functions are valid arrays
   - [ ] Check useEffect dependencies
   - [ ] Validate auto-advance conditions
   - [ ] Test edge cases

2. **Testing Protocol**
   - Test normal flow: file + text → auto-advance
   - Test edge cases: incomplete data → no advance
   - Test error conditions: failed upload → no advance
   - Verify console is clean

3. **Development Guidelines**
   - Use TypeScript easing type definitions
   - Implement defensive programming
   - Add comprehensive validation
   - Test with React.StrictMode enabled

## Related Issues

- **Tailwind CSS v4**: May cause similar styling issues
- **React 19 StrictMode**: Can expose race conditions
- **Component Lifecycle**: Proper cleanup required

## Escalation Criteria

Escalate to development team if:
- Issue persists after applying all fixes
- Multiple users report similar problems
- Performance degradation observed
- Build fails with animation errors

## Files Modified

1. `frontend/src/components/InputScreen.tsx` - Easing + auto-advance + validation
2. `frontend/src/components/ProcessingScreen.tsx` - Easing fix
3. `frontend/src/components/RevealScreen.tsx` - Easing fix
4. `frontend/src/components/ExportModal.tsx` - Easing fix

---

**Last Updated**: 2025-01-31  
**Severity**: Medium  
**Impact**: User Experience
