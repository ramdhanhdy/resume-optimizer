# Component Flashing/Disappearing Fix

## Problem Summary

Components were appearing briefly then disappearing, causing a "flashing" effect. This issue persisted even after Tailwind CSS styling was fixed.

## Root Causes Identified

### 1. Invalid Framer Motion Easing Function
- **Issue**: All components used `ease: 'swift'` in transition configs
- **Problem**: `'swift'` is not a valid Framer Motion easing string
- **Impact**: Animations may malfunction, skip, or cause unexpected behavior

### 2. Auto-Advance Logic Race Condition
- **Issue**: `useEffect` in InputScreen was triggering without proper validation
- **Problem**: Auto-advance could fire even if:
  - Resume upload failed
  - resumeText was empty or invalid
  - React.StrictMode caused double-rendering (React 19)
- **Impact**: Screen would advance prematurely before data was ready

### 3. Missing Defensive Checks
- **Issue**: `handleContinue` didn't validate data before advancing
- **Problem**: Could attempt to start processing with invalid/missing data
- **Impact**: Downstream errors and unexpected behavior

## Phase 1 Fixes Applied

### Fix 1: Corrected Framer Motion Easing

**Changed in 4 files:**
- `frontend/src/components/InputScreen.tsx`
- `frontend/src/components/ProcessingScreen.tsx`
- `frontend/src/components/RevealScreen.tsx`
- `frontend/src/components/ExportModal.tsx`

**Before:**
```tsx
transition={{ duration: 0.4, ease: 'swift' }}
```

**After:**
```tsx
transition={{ duration: 0.4, ease: [0.4, 0.0, 0.2, 1] }}
```

This matches the CSS custom property: `--ease-swift: cubic-bezier(0.4, 0.0, 0.2, 1);`

---

### Fix 2: Improved Auto-Advance Logic

**File:** `frontend/src/components/InputScreen.tsx`

**Before:**
```tsx
useEffect(() => {
  if (isReady && !isLoading) {
    const timeoutId = setTimeout(handleContinue, 1000);
    return () => clearTimeout(timeoutId);
  }
}, [isReady, isLoading]);
```

**After:**
```tsx
useEffect(() => {
  // Only auto-advance if we have BOTH ready state AND valid resume text
  if (isReady && !isLoading && resumeText.trim().length > 0) {
    const timeoutId = setTimeout(handleContinue, 1000);
    return () => clearTimeout(timeoutId);
  }
  // eslint-disable-next-line react-hooks/exhaustive-deps
}, [isReady, isLoading, resumeText]);
```

**Changes:**
1. Added `resumeText.trim().length > 0` check
2. Added `resumeText` to dependency array
3. Prevents auto-advance if resume upload failed or returned empty text

---

### Fix 3: Added Defensive Check in handleContinue

**File:** `frontend/src/components/InputScreen.tsx`

**Before:**
```tsx
const handleContinue = () => {
  if (isReady && resumeText) {
    const isUrl = jobInput.startsWith('http://') || jobInput.startsWith('https://');
    onStart({ resumeText, jobInput, isUrl });
  }
};
```

**After:**
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

**Changes:**
1. Added minimum length check (`> 10` characters)
2. Added console warning for debugging
3. Prevents advancing with trivially short or empty resume text

---

## Phase 2 (Optional - Not Applied)

If issues persist after Phase 1, consider:

### Option A: Temporarily Disable React.StrictMode
**File:** `frontend/src/index.tsx`

```tsx
// Remove StrictMode wrapper for development
const root = ReactDOM.createRoot(rootElement);
root.render(<App />);
```

**Note:** Only for debugging. Re-enable for production.

### Option B: Remove Auto-Advance Entirely
Remove the entire `useEffect` auto-advance logic and require manual button click only.

---

## Expected Outcomes

After Phase 1 fixes:
- ✅ Components render smoothly without flashing
- ✅ Animations transition correctly with proper easing
- ✅ Auto-advance only happens when resume is successfully uploaded
- ✅ No premature screen transitions
- ✅ Console warnings if user tries to advance without valid data

---

## Testing Instructions

1. **Clean start**: Clear browser cache and reload
2. **Test normal flow**:
   - Load page → InputScreen appears and stays visible
   - Type in job field → No flashing or disappearing
   - Click Upload → Select file
   - Wait for upload → Button shows checkmark with filename
   - After 1 second → Auto-advance to ProcessingScreen
   
3. **Test edge cases**:
   - Upload file BEFORE typing job text → Should not advance
   - Type job text BEFORE uploading → Should not advance
   - Upload fails (network error) → Should not advance
   - Cancel file dialog → Should not cause flashing

4. **Check console**: No warnings or errors

---

## Build Results

- **CSS size**: 19.73 kB (gzipped: 4.55 kB)
- **JS size**: 331.52 kB (gzipped: 105.73 kB)
- **Build time**: ~1.6s
- **Status**: ✅ Build successful

---

## Files Modified

1. `frontend/src/components/InputScreen.tsx` - Easing fix + auto-advance logic + defensive check
2. `frontend/src/components/ProcessingScreen.tsx` - Easing fix
3. `frontend/src/components/RevealScreen.tsx` - Easing fix
4. `frontend/src/components/ExportModal.tsx` - Easing fix

---

## Next Steps

1. Start dev server: `npm run dev`
2. Test in browser at `http://localhost:3000`
3. Verify components stay visible without flashing
4. If issue persists, proceed with Phase 2 options
5. Once confirmed working, start backend and test full integration
