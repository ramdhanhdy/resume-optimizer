@echo off
echo Starting Resume Optimizer Application...
echo.

REM Check if backend virtual environment exists
if not exist "backend\.venv\" (
    echo Error: Backend virtual environment not found.
    echo Please run setup first:
    echo   cd backend
    echo   uv venv
    echo   venv\Scripts\activate
    echo   uv pip install -r requirements.txt
    pause
    exit /b 1
)

REM Check if frontend node_modules exists
if not exist "frontend\node_modules\" (
    echo Error: Frontend dependencies not installed.
    echo Please run:
    echo   cd frontend
    echo   npm install
    pause
    exit /b 1
)

REM Start backend in new window
echo Starting backend server...
start "Resume Optimizer - Backend" cmd /k "cd backend && venv\Scripts\activate && python server.py"

REM Wait a bit for backend to start
timeout /t 3 /nobreak > nul

REM Start frontend in new window
echo Starting frontend server...
start "Resume Optimizer - Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo Application is starting...
echo Backend: http://localhost:8000
echo Frontend: http://localhost:3000
echo.
pause
