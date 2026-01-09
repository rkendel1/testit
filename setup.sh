#!/bin/bash
# Quick setup and validation script for TestIt

set -e

echo "==================================="
echo "TestIt - Setup and Validation"
echo "==================================="

# Check if Docker is installed
echo -e "\n1. Checking Docker installation..."
if command -v docker &> /dev/null; then
    echo "✓ Docker is installed: $(docker --version)"
else
    echo "✗ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
echo -e "\n2. Checking Docker Compose installation..."
if command -v docker-compose &> /dev/null; then
    echo "✓ Docker Compose is installed: $(docker-compose --version)"
elif docker compose version &> /dev/null; then
    echo "✓ Docker Compose (plugin) is installed: $(docker compose version)"
else
    echo "✗ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Check if Docker daemon is running
echo -e "\n3. Checking Docker daemon..."
if docker info &> /dev/null; then
    echo "✓ Docker daemon is running"
else
    echo "✗ Docker daemon is not running. Please start Docker first."
    exit 1
fi

# Check Python installation (optional for local dev)
echo -e "\n4. Checking Python installation (optional)..."
if command -v python3 &> /dev/null; then
    echo "✓ Python is installed: $(python3 --version)"
else
    echo "⚠ Python is not installed (only needed for local development)"
fi

# Check Node.js installation (optional for frontend dev)
echo -e "\n5. Checking Node.js installation (optional)..."
if command -v node &> /dev/null; then
    echo "✓ Node.js is installed: $(node --version)"
else
    echo "⚠ Node.js is not installed (only needed for frontend development)"
fi

echo -e "\n==================================="
echo "Setup Validation Complete!"
echo "==================================="

echo -e "\nNext steps:"
echo "1. Create .env file (optional): cp .env.example .env"
echo "2. Start services: docker-compose up --build"
echo "3. Access API: http://localhost:8000"
echo "4. View API docs: http://localhost:8000/docs"
echo "5. For frontend: cd frontend && npm install && npm start"

echo -e "\nReady to go! 🚀"
