# UI Testing Checklist

## Frontend Testing Steps

### 1. Visual Verification
Open `http://localhost:3000` and check:

- [ ] **Background color** is off-white (#FAFAF9), not pure white
- [ ] **Font** is system font (San Francisco/Segoe UI), not Times New Roman
- [ ] **"Transform Your Resume"** heading is visible and styled
- [ ] **Upload Resume button** has blue background (#0274BD)
- [ ] **Input field** has proper styling with border
- [ ] Components **don't flash or disappear** on load

### 2. Interaction Testing

#### Input Screen
- [ ] Click "Upload Resume" button - file dialog opens
- [ ] Select a PDF/DOCX file - button shows checkmark and filename
- [ ] Type in job posting field - input responds
- [ ] With both fields filled - "Continue" button appears smoothly
- [ ] Auto-advance after 1 second to Processing screen

#### Processing Screen
- [ ] Animated progress bar appears
- [ ] Phase indicators cycle through (Analyzing → Planning → Writing → Validating → Finalizing)
- [ ] Activity text updates dynamically
- [ ] Insights appear in grid layout on the right
- [ ] Progress reaches 100% and transitions to Reveal screen

#### Reveal Screen
- [ ] Header shows match score percentage
- [ ] "Before" and "After" columns display side-by-side
- [ ] Hover over info icons - popover appears with reason
- [ ] Warning indicators (orange dots) show on items with validation issues
- [ ] Scroll syncs between both columns
- [ ] "Download" button visible in header
- [ ] "Back" button returns to Input screen

### 3. Browser Console Check
Open DevTools Console (F12) and verify:
- [ ] No React errors (red text)
- [ ] No missing module errors
- [ ] No 404 errors for CSS/JS files
- [ ] No Tailwind configuration warnings
- [ ] Framer Motion loads without errors

### 4. Animation Quality
- [ ] Fade in/out transitions smooth between screens
- [ ] Upload button hover effect works
- [ ] Continue button appears with slide-up animation
- [ ] Processing bar animates smoothly
- [ ] Insight cards appear with stagger effect

### 5. Responsive Design (Optional)
- [ ] Resize window - layout adjusts
- [ ] Mobile viewport (375px) - UI doesn't break
- [ ] Tablet viewport (768px) - readable and functional

## Known Limitations (Not Yet Implemented)

⚠️ **Backend not connected** - Using mock data for testing:
- Resume upload simulates but doesn't process
- Processing screen shows animations only
- Reveal screen uses hardcoded dummy data

⚠️ **Resume diff parsing** - TODO in RevealScreen component
- Need to implement actual before/after comparison
- Currently shows bullet list placeholders

## Testing with Backend

Once backend is running on `http://localhost:8000`:

1. **Start backend**: 
   ```bash
   cd E:\resume-optimizer\backend
   .venv\Scripts\activate  # or: source .venv/bin/activate
   python server.py
   ```

2. **Start frontend**: 
   ```bash
   cd E:\resume-optimizer\frontend
   npm run dev
   ```

3. **Full flow test**:
   - Upload real resume file
   - Enter job posting URL or text
   - Verify API calls in Network tab
   - Check all 5 agents execute
   - Verify validation scores are real
   - Test DOCX/PDF export functionality

## Troubleshooting

### Components disappear after render
- Check browser console for React errors
- Verify CSS is loading (check Network tab)
- Check if `@import "tailwindcss"` is first line in index.css

### Styles not applying
- Rebuild: `npm run build`
- Clear browser cache (Ctrl+Shift+R)
- Check if custom colors are in `dist/assets/*.css`
- Verify Tailwind v4 theme configuration in index.css

### Animations choppy
- Check if Framer Motion is installed: `npm list framer-motion`
- Verify `AnimatePresence` has `mode="wait"` prop
- Check browser performance (disable extensions)

### Upload button doesn't work
- Check if `apiClient.uploadResume()` is implemented
- Verify backend is running and accessible
- Check CORS configuration in backend server.py
