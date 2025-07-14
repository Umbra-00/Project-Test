#!/bin/bash

# Umbra Personalized Learning Platform - Complete Startup Script
# This script ensures all components are properly configured and started

echo "🎯 Starting Umbra Personalized Learning Platform"
echo "=================================================="

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

print_status "Python 3 is available"

# Check if virtual environment exists, create if not
if [ ! -d "venv" ]; then
    print_info "Creating virtual environment..."
    python3 -m venv venv
    print_status "Virtual environment created"
else
    print_status "Virtual environment exists"
fi

# Activate virtual environment
print_info "Activating virtual environment..."
source venv/bin/activate

# Install/update requirements
print_info "Installing/updating requirements..."
pip install --upgrade pip
pip install -r requirements.txt
pip install -r frontend/requirements.txt

print_status "Requirements installed"

# Check if .env file exists
if [ ! -f ".env" ]; then
    print_warning ".env file not found. Creating from example..."
    if [ -f ".env.example" ]; then
        cp .env.example .env
        print_status ".env file created from example"
    else
        print_info "Creating basic .env file..."
        cat > .env << EOF
# Database Configuration
DATABASE_URL=postgresql://umbra_user:umbra_dev_password123@localhost:5432/umbra_db

# Security
SECRET_KEY=your-secret-key-here-change-in-production

# Environment
ENVIRONMENT=development

# API Configuration
FASTAPI_BASE_URL=http://localhost:8000
EOF
        print_status "Basic .env file created"
    fi
else
    print_status ".env file exists"
fi

# Test backend imports
print_info "Testing backend imports..."
if python -c "from src.api.v1.main import app; print('Backend imports successful')" 2>/dev/null; then
    print_status "Backend imports successful"
else
    print_error "Backend import failed. Please check dependencies."
    exit 1
fi

# Test frontend imports
print_info "Testing frontend imports..."
if python -c "import streamlit; import plotly.express; print('Frontend imports successful')" 2>/dev/null; then
    print_status "Frontend imports successful"
elif python -c "import streamlit; print('Frontend imports successful (plotly optional)')" 2>/dev/null; then
    print_warning "Frontend imports successful (plotly charts will be disabled)"
else
    print_error "Frontend import failed. Please check dependencies."
    exit 1
fi

# Check authentication service
print_info "Testing authentication service..."
if python -c "from src.services.auth_service import AuthService; print('Auth service imports successful')" 2>/dev/null; then
    print_status "Authentication service ready"
else
    print_error "Authentication service import failed."
    exit 1
fi

echo ""
echo "🎉 Umbra Personalized Learning Platform is ready!"
echo "=================================================="
echo ""
echo "🚀 To start the platform:"
echo ""
echo "   Backend:  uvicorn src.api.v1.main:app --host 0.0.0.0 --port 8000 --reload"
echo "   Frontend: streamlit run frontend/app.py --server.port 8501"
echo ""
echo "🌐 Access URLs:"
echo "   Frontend: http://localhost:8501"
echo "   Backend:  http://localhost:8000"
echo "   API Docs: http://localhost:8000/api/v1/docs"
echo ""
echo "🎯 New Features Available:"
echo "   ✅ User Authentication (Login/Register)"
echo "   ✅ Personalized Dashboard"
echo "   ✅ Learning Analytics"
echo "   ✅ Course Recommendations"
echo "   ✅ Progress Tracking"
echo "   ✅ Business Intelligence APIs"
echo ""
echo "📊 Demo Features (even without database):"
echo "   - Authentication UI"
echo "   - Dashboard Layout"
echo "   - Personalization Forms"
echo "   - Analytics Visualization"
echo ""
echo "💡 Note: Some features require database connection for full functionality."
echo "     The UI and authentication system work independently."
echo ""

# Provide option to start services
read -p "Would you like to start the services now? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    print_info "Starting backend..."
    uvicorn src.api.v1.main:app --host 0.0.0.0 --port 8000 --reload &
    BACKEND_PID=$!
    
    sleep 3
    
    print_info "Starting frontend..."
    streamlit run frontend/app.py --server.port 8501 --server.address 0.0.0.0 &
    FRONTEND_PID=$!
    
    sleep 2
    
    echo ""
    print_status "Platform started successfully!"
    echo ""
    echo "🌐 Access your platform at: http://localhost:8501"
    echo ""
    echo "🛑 To stop: Press Ctrl+C or run 'pkill -f \"uvicorn\\|streamlit\"'"
    
    # Keep script running
    wait $BACKEND_PID $FRONTEND_PID
else
    echo ""
    print_info "Services not started. Use the commands above to start manually."
fi
