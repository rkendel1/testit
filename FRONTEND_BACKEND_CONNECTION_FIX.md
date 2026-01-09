# Frontend-Backend Connection Fix

## Problem Summary

Users were experiencing connection failures when trying to access the backend API:

```bash
$ curl http://localhost:8000/health
curl: (56) Recv failure: Connection reset by peer

$ curl http://127.0.0.1:8000/health
curl: (28) Failed to connect to 127.0.0.1 port 8000 after 7844 ms: Couldn't connect to server
```

Frontend showed error:
```
Error: Failed to submit (504): Error occurred while trying to proxy: 127.0.0.1:3000/api/submit
```

## Root Cause

The issue had **two** potential causes:

### 1. Backend Not Running (Primary Issue)
The most common cause is that the backend API server is not running on port 8000. The `curl` errors confirm this - the backend is simply not accessible.

### 2. Proxy Configuration (Secondary Issue - Now Fixed)
Previously, `frontend/src/setupProxy.js` defaulted to `http://api:8000` (Docker service name), which only works inside Docker Compose. When accessed via browser at `localhost:3000` or `127.0.0.1:3000`, the Node.js proxy tried to reach `http://api:8000` - a hostname that doesn't exist outside Docker.

## Solution

### Fix 1: Ensure Backend is Running

The backend must be running on port 8000. You have two options:

#### Option A: Using Docker Compose (Recommended)

```bash
# From the project root
docker compose up -d
```

This starts all services:
- `api` - Backend API on port 8000
- `frontend` - Frontend on port 3000
- `redis` - Redis cache
- `celery-worker` - Background task worker
- `celery-beat` - Periodic task scheduler

Verify services are running:
```bash
docker compose ps

# Should show all services as "running"
```

Test backend health:
```bash
curl http://localhost:8000/health
# Should return: {"status":"healthy"}
```

#### Option B: Running Services Manually

**Terminal 1 - Start Redis:**
```bash
docker run -d -p 6379:6379 redis:7-alpine
```

**Terminal 2 - Start Backend:**
```bash
cd /path/to/testit
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

**Terminal 3 - Start Celery Worker:**
```bash
cd /path/to/testit
celery -A app.celery_app worker --loglevel=info
```

**Terminal 4 - Start Frontend:**
```bash
cd frontend
npm install
npm start
```

### Fix 2: Proxy Configuration (Already Fixed)

The proxy configuration in `frontend/src/setupProxy.js` has been updated to:
- **Default to `http://localhost:8000`** - Works both inside and outside Docker
- **Respect `REACT_APP_PROXY_TARGET` env var** - Override when running in Docker Compose
- **Provide better error messages** - Clear guidance when backend is unreachable

## How It Works Now

### Running with Docker Compose
```yaml
# docker-compose.yml sets this environment variable
frontend:
  environment:
    - REACT_APP_PROXY_TARGET=http://api:8000  # Use Docker service name
```

The proxy will use `http://api:8000` (Docker internal network).

### Running Locally (npm start)
When you run `npm start` in the `frontend` directory without Docker, the proxy defaults to `http://localhost:8000`.

## Verification Steps

### 1. Check Backend is Running

```bash
# Test backend directly
curl http://localhost:8000/health

# Should return:
# {"status":"healthy"}
```

### 2. Check Frontend Can Reach Backend

```bash
# With frontend running, test proxy
curl http://localhost:3000/health

# Should also return:
# {"status":"healthy"}
```

### 3. Test Full Workflow

1. Open browser to `http://localhost:3000`
2. Check header shows:
   - **API**: `http://localhost:8000`
   - **Status**: `✓ Healthy` (green checkmark)
3. Submit a test repository:
   ```
   https://github.com/docker/welcome-to-docker
   ```
4. Should see build progress without 504 errors

## Troubleshooting

### Error: "Connection refused" or "Connection reset by peer"

**Cause**: Backend is not running

**Solution**:
```bash
# Check if backend is running
curl http://localhost:8000/health

# If not running, start it:
docker compose up -d api

# Or manually:
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Error: "Failed to connect to 127.0.0.1 port 8000"

**Cause**: Backend is not running or not listening on port 8000

**Solution**:
```bash
# Check what's running on port 8000
lsof -i :8000  # macOS/Linux
netstat -ano | findstr :8000  # Windows

# If nothing, start backend:
docker compose up -d api
```

### Error: "504: Error occurred while trying to proxy"

**Cause**: Frontend proxy cannot reach backend

**Solution**:
1. Verify backend is running: `curl http://localhost:8000/health`
2. Check frontend logs for proxy target:
   ```
   [Proxy] Configuring proxy to target: http://localhost:8000
   ```
3. If target is wrong, set environment variable:
   ```bash
   # For Docker Compose (already set in docker-compose.yml)
   REACT_APP_PROXY_TARGET=http://api:8000

   # For local development (default is already localhost)
   REACT_APP_PROXY_TARGET=http://localhost:8000
   ```

### Frontend shows "✗ Unavailable"

**Cause**: Health check failing

**Solution**:
1. Open browser console (F12)
2. Look for errors in Network tab
3. Check if `/health` request succeeds
4. Verify backend is running: `curl http://localhost:8000/health`

## Configuration Reference

### docker-compose.yml (Default)
```yaml
frontend:
  environment:
    - REACT_APP_API_URL=http://localhost:8000       # For browser requests
    - REACT_APP_PROXY_TARGET=http://api:8000        # For proxy requests
```

### frontend/.env (Local Development)
```bash
# Browser-side requests
REACT_APP_API_URL=http://localhost:8000

# Proxy target (optional, defaults to http://localhost:8000)
# REACT_APP_PROXY_TARGET=http://localhost:8000
```

### frontend/src/setupProxy.js
```javascript
// Priority:
// 1. PROXY_TARGET env var (override)
// 2. REACT_APP_PROXY_TARGET env var (docker-compose)
// 3. Default: http://localhost:8000 (local development)

const target = process.env.PROXY_TARGET || 
               process.env.REACT_APP_PROXY_TARGET || 
               'http://localhost:8000';
```

## Summary of Changes

**Before:**
- Proxy defaulted to `http://api:8000` (Docker service name)
- Failed when running outside Docker
- Generic error messages

**After:**
- Proxy defaults to `http://localhost:8000` (works everywhere)
- Override with `REACT_APP_PROXY_TARGET` in Docker Compose
- Helpful error messages with troubleshooting hints

## Quick Reference

| Scenario | Backend URL | Proxy Target | How to Set |
|----------|-------------|--------------|------------|
| Docker Compose | `http://api:8000` | `http://api:8000` | Set in `docker-compose.yml` (already done) |
| Local npm start | `http://localhost:8000` | `http://localhost:8000` | Default (no config needed) |
| Mixed (Docker backend, local frontend) | `http://localhost:8000` | `http://localhost:8000` | Default (no config needed) |

## Need Help?

If you're still experiencing issues:

1. **Check all services are running:**
   ```bash
   docker compose ps
   ```

2. **View logs:**
   ```bash
   docker compose logs -f api
   docker compose logs -f frontend
   ```

3. **Restart services:**
   ```bash
   docker compose down
   docker compose up -d
   ```

4. **Full reset:**
   ```bash
   docker compose down -v
   docker system prune -f
   docker compose up --build
   ```
