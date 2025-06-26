#!/bin/bash

# Start Flask backend
echo "Starting Flask backend..."
cd backend
python app.py &
BACKEND_PID=$!

# Wait a moment for backend to start
sleep 3

# Start React frontend
echo "Starting React frontend..."
cd ../frontend
npm start &
FRONTEND_PID=$!

echo "Development servers started!"
echo "Flask backend: http://localhost:5000"
echo "React frontend: http://localhost:3000"
echo ""
echo "Press Ctrl+C to stop both servers"

# Wait for user to stop
wait

# Cleanup
kill $BACKEND_PID
kill $FRONTEND_PID
echo "Servers stopped." 