#!/bin/bash

echo "Starting Resume Optimizer Application..."
echo ""

# Check if backend virtual environment exists
if [ ! -d "backend/.venv" ]; then
    echo "Error: Backend virtual environment not found."
    echo "Please run setup first:"
    echo "  cd backend"
    echo "  uv venv"
    echo "  source .venv/bin/activate"
    echo "  uv pip install -r requirements.txt"
    exit 1
fi

# Check if frontend node_modules exists
if [ ! -d "frontend/node_modules" ]; then
    echo "Error: Frontend dependencies not installed."
    echo "Please run:"
    echo "  cd frontend"
    echo "  npm install"
    exit 1
fi

# Start backend in background
echo "Starting backend server..."
cd backend
source venv/bin/activate
python server.py &
BACKEND_PID=$!
cd ..

# Wait a bit for backend to start
sleep 3

# Start frontend in background
echo "Starting frontend server..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "Application is running..."
echo "Backend: http://localhost:8000"
echo "Frontend: http://localhost:3000"
echo ""
echo "Press Ctrl+C to stop both servers"
echo ""

# Wait for Ctrl+C
trap "kill $BACKEND_PID $FRONTEND_PID; exit" INT
wait
