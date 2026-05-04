# Setup Guide

Quick start guide for the Resume Optimizer application.

## Initial Setup

### Backend Setup

1. **Navigate to backend directory**
   ```bash
   cd backend
   ```

2. **Create virtual environment using uv**
   ```bash
   uv venv
   ```

3. **Activate virtual environment**
   
   Windows (CMD):
   ```bash
   .\.venv\Scripts\activate
   ```

   Windows (PowerShell):
   ```bash
   .\.venv\Scripts\Activate.ps1
   ```

   macOS/Linux:
   ```bash
   source .venv/bin/activate
   ```

4. **Install dependencies**
   ```bash
   uv pip install -r requirements.txt
   ```

5. **Configure environment variables**
   
   Copy `.env.example` to `.env`:
   ```bash
   copy .env.example .env  # Windows
   cp .env.example .env    # macOS/Linux
   ```
   
   Edit `.env` and add your API keys:
   ```
   OPENROUTER_API_KEY=your_openrouter_key_here
   EXA_API_KEY=your_exa_key_here
   ```

6. **Create data directory**
   ```bash
   mkdir data
   ```

### Frontend Setup

1. **Navigate to frontend directory**
   ```bash
   cd frontend
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Configure environment (optional)**
   
   Copy `.env.example` to `.env.local`:
   ```bash
   copy .env.example .env.local  # Windows
   cp .env.example .env.local    # macOS/Linux
   ```
   
   The default settings should work if backend runs on port 8000.

## Running the Application

### Option 1: Use Startup Scripts (Recommended)

Windows:
```bash
start.bat
```

macOS/Linux:
```bash
chmod +x start.sh
./start.sh
```

### Option 2: Manual Start

**Terminal 1 - Backend:**
```bash
cd backend
venv\Scripts\activate  # Windows
# OR
source venv/bin/activate  # macOS/Linux

python server.py
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

### Access the Application

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## Troubleshooting

### Backend Issues

**Import Error: No module named 'fastapi'**
- Solution: Activate venv and reinstall dependencies
  ```bash
  cd backend
  source .venv/bin/activate  # or .\.venv\Scripts\activate on Windows
  uv pip install -r requirements.txt
  ```

**Port 8000 already in use**
- Solution: Change PORT in `backend/.env`
  ```
  PORT=8001
  ```
  Also update `frontend/.env.local`:
  ```
  VITE_API_URL=http://localhost:8001
  ```

**API Key Error**
- Solution: Ensure API keys are set in `backend/.env`
- Get OpenRouter key: https://openrouter.ai/keys
- Get Exa key: https://exa.ai/

### Frontend Issues

**Module not found errors**
- Solution: Reinstall dependencies
  ```bash
  cd frontend
  rm -rf node_modules package-lock.json
  npm install
  ```

**Cannot connect to backend**
- Solution: Ensure backend is running on http://localhost:8000
- Check `frontend/.env.local` has correct VITE_API_URL
- Check browser console for CORS errors

**Port 3000 already in use**
- Vite will automatically try the next available port
- Or specify in `frontend/vite.config.ts`:
  ```typescript
  server: {
    port: 3001,
    ...
  }
  ```

### Database Issues

**Database file not found**
- The database is created automatically on first run
- Location: `backend/data/applications.db`
- If issues persist, delete and restart the backend

## Development Tips

### Backend Development

- **Auto-reload:** Use uvicorn's reload flag
  ```bash
  uvicorn server:app --reload --port 8000
  ```

- **API Documentation:** Visit http://localhost:8000/docs for interactive API docs

- **Database inspection:** Use SQLite browser or:
  ```bash
  sqlite3 data/applications.db
  ```

### Frontend Development

- **Hot Module Replacement:** Vite provides instant updates
- **TypeScript checking:** Run `npm run build` to check for type errors
- **Component development:** Each component is in `src/components/`

## Next Steps

1. Upload a resume (PDF or DOCX)
2. Paste a job posting URL or text
3. Watch the AI pipeline process your resume
4. Review the optimized version
5. Download the result

## Getting Help

- Check the main README.md for detailed documentation
- Review API endpoints at http://localhost:8000/docs
- Check browser console for frontend errors
- Check terminal output for backend errors

## Updating

To pull latest changes and update:

```bash
# Update backend
cd backend
source .venv/bin/activate  # or .\.venv\Scripts\activate on Windows
uv pip install -r requirements.txt --upgrade

# Update frontend
cd frontend
npm install
```
