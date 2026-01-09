#!/bin/bash
# Validation script to check if all files are in place

echo "==================================="
echo "TestIt - File Structure Validation"
echo "==================================="

# Check critical files
echo -e "\n1. Checking critical files..."

critical_files=(
    "README.md"
    "QUICKSTART.md"
    "ARCHITECTURE.md"
    "DEVELOPMENT.md"
    "EXAMPLES.md"
    "LICENSE"
    "Makefile"
    "docker-compose.yml"
    "Dockerfile"
    "requirements.txt"
    ".gitignore"
    ".env.example"
    "setup.sh"
    "test_api.sh"
)

missing_files=0
for file in "${critical_files[@]}"; do
    if [ -f "$file" ]; then
        echo "  ✓ $file"
    else
        echo "  ✗ $file (MISSING)"
        missing_files=$((missing_files + 1))
    fi
done

# Check backend files
echo -e "\n2. Checking backend files..."

backend_files=(
    "app/__init__.py"
    "app/main.py"
    "app/config.py"
    "app/models.py"
    "app/celery_app.py"
    "app/tasks.py"
    "app/language_detector.py"
    "app/dockerfile_generator.py"
    "app/docker_orchestrator.py"
    "app/session_manager.py"
    "app/terminal_manager.py"
)

for file in "${backend_files[@]}"; do
    if [ -f "$file" ]; then
        echo "  ✓ $file"
    else
        echo "  ✗ $file (MISSING)"
        missing_files=$((missing_files + 1))
    fi
done

# Check frontend files
echo -e "\n3. Checking frontend files..."

frontend_files=(
    "frontend/package.json"
    "frontend/.gitignore"
    "frontend/public/index.html"
    "frontend/src/index.js"
    "frontend/src/App.js"
    "frontend/src/App.css"
    "frontend/src/Terminal.js"
    "frontend/src/Terminal.css"
    "frontend/src/index.css"
)

for file in "${frontend_files[@]}"; do
    if [ -f "$file" ]; then
        echo "  ✓ $file"
    else
        echo "  ✗ $file (MISSING)"
        missing_files=$((missing_files + 1))
    fi
done

# Summary
echo -e "\n==================================="
if [ $missing_files -eq 0 ]; then
    echo "✅ All files present! ($((${#critical_files[@]} + ${#backend_files[@]} + ${#frontend_files[@]})) files checked)"
    echo "==================================="
    echo -e "\nProject structure is complete!"
    echo -e "\nNext steps:"
    echo "  1. Run './setup.sh' to validate environment"
    echo "  2. Run 'make up' to start services"
    echo "  3. Read QUICKSTART.md for usage instructions"
    exit 0
else
    echo "❌ Missing $missing_files file(s)"
    echo "==================================="
    exit 1
fi
