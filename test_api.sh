#!/bin/bash

echo "Testing TestIt API..."

API_URL="http://localhost:8000"

# Test health check
echo -e "\n1. Testing health check..."
curl -s "$API_URL/health" | python -m json.tool

# Test root endpoint
echo -e "\n2. Testing root endpoint..."
curl -s "$API_URL/" | python -m json.tool

# Test submit endpoint with a sample repo
echo -e "\n3. Submitting a test repository..."
TASK_RESPONSE=$(curl -s -X POST "$API_URL/api/submit" \
  -H "Content-Type: application/json" \
  -d '{"repo_url": "https://github.com/docker/welcome-to-docker"}')

echo "$TASK_RESPONSE" | python -m json.tool

TASK_ID=$(echo "$TASK_RESPONSE" | python -c "import sys, json; print(json.load(sys.stdin).get('task_id', ''))")

if [ -n "$TASK_ID" ]; then
  echo -e "\nTask ID: $TASK_ID"
  
  echo -e "\n4. Checking task status..."
  sleep 2
  curl -s "$API_URL/api/status/$TASK_ID" | python -m json.tool
  
  echo -e "\n5. Listing active sessions..."
  sleep 2
  curl -s "$API_URL/api/sessions" | python -m json.tool
else
  echo "Failed to get task ID"
fi

echo -e "\nTest complete!"
