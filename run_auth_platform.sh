#!/bin/bash

# Umbra Personalized Learning Platform - Enhanced Startup Script
# This script starts the complete personalized learning platform with authentication

echo "🎯 Starting Umbra Personalized Learning Platform"
echo "=================================================="

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "🔧 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install/update requirements
echo "📦 Installing requirements..."
pip install -r requirements.txt
pip install -r frontend/requirements.txt

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found. Creating from example..."
    cp .env.example .env
    echo "✅ Please update .env file with your configurations"
fi

# Run database migrations
echo "🗄️  Running database migrations..."
python -m alembic upgrade head

# Start the backend in the background
echo "🚀 Starting FastAPI backend..."
uvicorn src.api.v1.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

# Wait for backend to start
echo "⏳ Waiting for backend to start..."
sleep 5

# Check if backend is running
if ! curl -s http://localhost:8000/api/v1/health > /dev/null; then
    echo "❌ Backend failed to start. Check logs above."
    kill $BACKEND_PID 2>/dev/null
    exit 1
fi

echo "✅ Backend started successfully at http://localhost:8000"
echo "📚 API Documentation: http://localhost:8000/api/v1/docs"

# Start the enhanced frontend
echo "🖥️  Starting Enhanced Streamlit Frontend..."
echo "🎯 Features:"
echo "   - User Authentication (Login/Register)"
echo "   - Personalized Dashboard"
echo "   - AI-Powered Recommendations"
echo "   - Learning Analytics"
echo "   - Progress Tracking"
echo "   - Business Intelligence"

streamlit run frontend/auth_app.py --server.port 8501 --server.address 0.0.0.0 &
FRONTEND_PID=$!

# Wait for frontend to start
echo "⏳ Waiting for frontend to start..."
sleep 3

echo ""
echo "🎉 Umbra Personalized Learning Platform is now running!"
echo "=================================================="
echo ""
echo "🖥️  Frontend (Enhanced UI): http://localhost:8501"
echo "🔧 Backend API: http://localhost:8000"
echo "📖 API Documentation: http://localhost:8000/api/v1/docs"
echo ""
echo "🎯 New Features:"
echo "   ✅ User Authentication & Registration"
echo "   ✅ Personalized Learning Dashboard"
echo "   ✅ AI-Powered Course Recommendations"
echo "   ✅ Learning Analytics & Insights"
echo "   ✅ Progress Tracking & Visualization"
echo "   ✅ Business Intelligence APIs"
echo "   ✅ User Interaction Tracking"
echo "   ✅ Adaptive Learning Paths"
echo ""
echo "👤 Demo Users (or register new ones):"
echo "   Username: demo_student / Password: demo123"
echo "   Username: demo_instructor / Password: demo123"
echo ""
echo "🛑 To stop the platform: Press Ctrl+C or run 'pkill -f \"uvicorn\\|streamlit\"'"
echo ""

# Keep the script running
wait $BACKEND_PID $FRONTEND_PID
