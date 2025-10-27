# First-Time Setup Checklist

Use this checklist when setting up the Resume Optimizer for the first time.

## Prerequisites
- [ ] Python 3.11 or higher installed
- [ ] Node.js 18 or higher installed
- [ ] npm or yarn package manager
- [ ] Git (optional, for version control)
- [ ] OpenRouter API key ([Get here](https://openrouter.ai/keys))
- [ ] Exa API key ([Get here](https://exa.ai/)) - Optional

## Backend Setup

### 1. Environment Setup
- [ ] Navigate to `backend/` directory
- [ ] Create virtual environment: `python -m venv venv`
- [ ] Activate virtual environment:
  - Windows: `venv\Scripts\activate`
  - macOS/Linux: `source venv/bin/activate`
- [ ] Install dependencies: `pip install -r requirements.txt`

### 2. Configuration
- [ ] Copy `.env.example` to `.env`
- [ ] Add OpenRouter API key to `.env`
- [ ] Add Exa API key to `.env` (optional)
- [ ] Create `data/` directory: `mkdir data`

### 3. Verification
- [ ] Run: `python -c "import fastapi; print('FastAPI installed')""`
- [ ] Run: `python -c "from src.agents import JobAnalyzerAgent; print('Agents loaded')"`
- [ ] Check prompts exist: `dir prompts` or `ls prompts`

## Frontend Setup

### 1. Dependency Installation
- [ ] Navigate to `frontend/` directory
- [ ] Install packages: `npm install`
- [ ] Verify installation: `npm list react`

### 2. Configuration
- [ ] Copy `.env.example` to `.env.local`
- [ ] Verify `VITE_API_URL=http://localhost:8000`

### 3. Verification
- [ ] Check TypeScript: `npx tsc --version`
- [ ] Check Vite: `npx vite --version`

## First Launch

### Option A: Using Startup Scripts
- [ ] Windows: Run `start.bat`
- [ ] macOS/Linux: Run `chmod +x start.sh && ./start.sh`

### Option B: Manual Launch
- [ ] **Terminal 1:** Start backend
  ```bash
  cd backend
  venv\Scripts\activate  # or source venv/bin/activate
  python server.py
  ```
- [ ] **Terminal 2:** Start frontend
  ```bash
  cd frontend
  npm run dev
  ```

## Verification Tests

### Backend Tests
- [ ] Open http://localhost:8000
- [ ] Should see: `{"message": "Resume Optimizer API", "version": "1.0.0"}`
- [ ] Open http://localhost:8000/docs
- [ ] Should see: Interactive API documentation

### Frontend Tests
- [ ] Open http://localhost:3000
- [ ] Should see: "Transform Your Resume" heading
- [ ] Should see: Upload button and job input field
- [ ] No console errors in browser DevTools

### Integration Tests
- [ ] Upload a test resume file (PDF or DOCX)
- [ ] Should see: File name appear, "Processing resume..." message
- [ ] Enter test job posting text
- [ ] Should see: "Continue" button appears
- [ ] Click Continue
- [ ] Should see: Processing screen with animated progress
- [ ] Wait for completion (~30-60 seconds)
- [ ] Should see: Reveal screen with before/after comparison
- [ ] Should see: Job match score displayed
- [ ] Click Download button
- [ ] Should see: Export modal opens

## Troubleshooting Checklist

### If Backend Fails to Start
- [ ] Check Python version: `python --version` (should be 3.11+)
- [ ] Check venv is activated (prompt should show `(venv)`)
- [ ] Reinstall dependencies: `pip install -r requirements.txt --force-reinstall`
- [ ] Check for port conflicts: Try changing PORT in `.env`
- [ ] Check `.env` file exists and has API keys
- [ ] Look for error messages in terminal

### If Frontend Fails to Start
- [ ] Check Node version: `node --version` (should be 18+)
- [ ] Delete `node_modules` and reinstall: `rm -rf node_modules && npm install`
- [ ] Check for port conflicts (Vite will auto-increment)
- [ ] Clear Vite cache: `rm -rf .vite`
- [ ] Look for error messages in terminal

### If API Calls Fail
- [ ] Backend is running on port 8000
- [ ] Frontend `.env.local` has correct VITE_API_URL
- [ ] Check browser Network tab for failed requests
- [ ] Check backend terminal for error logs
- [ ] Verify OpenRouter API key is valid
- [ ] Check OpenRouter account has credits

### If File Upload Fails
- [ ] File is PDF or DOCX format
- [ ] File size is reasonable (< 10MB)
- [ ] Check backend logs for extraction errors
- [ ] Try different file format
- [ ] Ensure `python-docx` and `pillow` are installed

### If Processing Hangs
- [ ] Check backend terminal for errors
- [ ] Verify OpenRouter API is responding
- [ ] Check browser console for JavaScript errors
- [ ] Refresh page and try again
- [ ] Check API key has sufficient credits

## Post-Setup Tasks

### Optional: Set Up Git
- [ ] Initialize git: `git init`
- [ ] Add files: `git add .`
- [ ] Commit: `git commit -m "Initial commit of integrated app"`

### Optional: Test Different Models
- [ ] Backend supports multiple LLM models
- [ ] Can configure in code or via API requests
- [ ] See OpenRouter docs for available models

### Optional: Customize Prompts
- [ ] Agent prompts are in `backend/prompts/`
- [ ] Can edit to adjust agent behavior
- [ ] Restart backend after changes

### Optional: Configure GitHub Integration
- [ ] Get GitHub personal access token
- [ ] Add to backend `.env`: `GITHUB_TOKEN=...`
- [ ] Enables portfolio project curation feature

## Success Criteria

✅ Backend running without errors
✅ Frontend accessible in browser
✅ Can upload resume successfully
✅ Can enter job posting
✅ Processing completes all 5 agents
✅ Results displayed in reveal screen
✅ Export functionality works

## Next Steps After Setup

1. **Read Documentation**
   - Review `README.md` for detailed features
   - Check `SETUP.md` for advanced configuration
   - Read `INTEGRATION_SUMMARY.md` to understand architecture

2. **Test with Real Data**
   - Upload your actual resume
   - Use a real job posting
   - Review the optimization suggestions
   - Try exporting in different formats

3. **Customize (Optional)**
   - Adjust agent prompts for your needs
   - Configure preferred LLM models
   - Customize UI styling
   - Add additional features

4. **Deploy (Optional)**
   - Consider containerizing with Docker
   - Deploy backend to cloud (Heroku, Railway, etc.)
   - Deploy frontend to Vercel or Netlify
   - Set up environment variables on hosting platform

## Support

If you encounter issues not covered here:
1. Check the error messages carefully
2. Review the troubleshooting section in `README.md`
3. Ensure all prerequisites are met
4. Try the manual setup steps instead of scripts
5. Check API service status (OpenRouter, Exa)

## Notes

- First run may take longer as database is created
- Some LLM models may be slower than others
- File processing time depends on file size
- Progress bar is estimated, actual time varies
- Export features require system libraries

---

✅ Once all items are checked, your Resume Optimizer is ready to use!
