#!/bin/bash

# Test script to verify frontend-backend connection

echo "======================================"
echo "Frontend-Backend Connection Test"
echo "======================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test 1: Check if backend is running
echo "Test 1: Checking if backend is accessible..."
if curl -s -f http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Backend is running on http://localhost:8000"
    BACKEND_RESPONSE=$(curl -s http://localhost:8000/health)
    echo "   Response: $BACKEND_RESPONSE"
else
    echo -e "${RED}✗${NC} Backend is NOT accessible on http://localhost:8000"
    echo "   ${YELLOW}Action required:${NC} Start backend with: docker compose up -d api"
    exit 1
fi

echo ""

# Test 2: Check backend root endpoint
echo "Test 2: Checking backend root endpoint..."
BACKEND_ROOT=$(curl -s http://localhost:8000/)
if echo "$BACKEND_ROOT" | grep -q "TestIt"; then
    echo -e "${GREEN}✓${NC} Backend root endpoint is responding"
    echo "   Message: $(echo $BACKEND_ROOT | jq -r '.message' 2>/dev/null || echo 'OK')"
else
    echo -e "${RED}✗${NC} Backend root endpoint not responding correctly"
fi

echo ""

# Test 3: Check if frontend is running
echo "Test 3: Checking if frontend is accessible..."
if curl -s -f http://localhost:3000/ > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Frontend is running on http://localhost:3000"
else
    echo -e "${YELLOW}!${NC} Frontend is NOT running on http://localhost:3000"
    echo "   This is expected if you haven't started the frontend yet"
    echo "   To start: docker compose up -d frontend (or cd frontend && npm start)"
fi

echo ""

# Test 4: Check frontend proxy (only if frontend is running)
if curl -s -f http://localhost:3000/ > /dev/null 2>&1; then
    echo "Test 4: Checking frontend proxy to backend..."
    if curl -s -f http://localhost:3000/health > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} Frontend proxy is working"
        PROXY_RESPONSE=$(curl -s http://localhost:3000/health)
        echo "   Proxied response: $PROXY_RESPONSE"
    else
        echo -e "${RED}✗${NC} Frontend proxy is NOT working"
        echo "   ${YELLOW}Check frontend logs for proxy errors${NC}"
    fi
    echo ""
fi

# Test 5: Check Docker services (if using docker compose)
echo "Test 5: Checking Docker Compose services..."
if command -v docker &> /dev/null; then
    if docker compose ps 2>/dev/null | grep -q "testit"; then
        echo -e "${GREEN}✓${NC} Docker Compose services found:"
        docker compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null | head -10
    else
        echo -e "${YELLOW}!${NC} No Docker Compose services detected"
        echo "   Run: docker compose up -d"
    fi
else
    echo -e "${YELLOW}!${NC} Docker not installed or not in PATH"
fi

echo ""
echo "======================================"
echo "Summary"
echo "======================================"

# Final verdict
if curl -s -f http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}Backend is accessible ✓${NC}"
    
    if curl -s -f http://localhost:3000/ > /dev/null 2>&1; then
        if curl -s -f http://localhost:3000/health > /dev/null 2>&1; then
            echo -e "${GREEN}Frontend proxy is working ✓${NC}"
            echo ""
            echo -e "${GREEN}Everything is working correctly!${NC}"
            echo ""
            echo "Next steps:"
            echo "1. Open http://localhost:3000 in your browser"
            echo "2. Submit a test repository (e.g., https://github.com/docker/welcome-to-docker)"
            echo "3. Wait for the build to complete"
            echo "4. Access the terminal once ready"
        else
            echo -e "${RED}Frontend proxy is NOT working ✗${NC}"
            echo ""
            echo "Frontend is running but cannot proxy to backend."
            echo "Check frontend logs for proxy errors."
        fi
    else
        echo -e "${YELLOW}Frontend is not running${NC}"
        echo ""
        echo "Backend is ready. Start frontend with:"
        echo "  docker compose up -d frontend"
        echo "  OR"
        echo "  cd frontend && npm start"
    fi
else
    echo -e "${RED}Backend is NOT accessible ✗${NC}"
    echo ""
    echo "Start backend with:"
    echo "  docker compose up -d"
    echo "  OR"
    echo "  uvicorn app.main:app --host 0.0.0.0 --port 8000"
fi

echo ""
