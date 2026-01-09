# CORS and Network Troubleshooting Guide

This guide helps resolve common CORS and network connectivity issues when running TestIt.

## Quick Checks

### 1. Verify All Services Are Running

```bash
docker compose ps
```

You should see:
- `redis` - running
- `api` - running on port 8000
- `celery-worker` - running
- `celery-beat` - running
- `frontend` - running on port 3000

### 2. Check API Health

```bash
curl http://localhost:8000/health
```

Should return: `{"status":"healthy"}`

### 3. Check Frontend Access

Open http://localhost:3000 in your browser. You should see the TestIt UI with:
- API URL displayed in the header
- Health status showing "✓ Healthy"

## Common Issues and Solutions

### Issue 1: "Cannot connect to backend API"

**Symptoms:**
- Frontend shows "API: http://localhost:8000" but health status is "✗ Unavailable"
- Submit repository fails with "Cannot connect to backend API"

**Solutions:**

1. **Check if API container is running:**
   ```bash
   docker compose logs api
   ```
   
2. **Restart the API service:**
   ```bash
   docker compose restart api
   ```

3. **Check port 8000 is not in use by another process:**
   ```bash
   lsof -i :8000  # On macOS/Linux
   netstat -ano | findstr :8000  # On Windows
   ```

4. **Verify API is accessible:**
   ```bash
   curl http://localhost:8000/
   ```

### Issue 2: WebSocket Connection Failed

**Symptoms:**
- Terminal shows "WebSocket error: Connection failed"
- Browser console shows WebSocket connection errors

**Solutions:**

1. **Check WebSocket URL construction:**
   - The frontend should construct: `ws://localhost:8000/api/terminal/{session_id}`
   - Check browser console for the WebSocket URL being used

2. **Verify the session exists:**
   ```bash
   curl http://localhost:8000/api/sessions
   ```

3. **Check API logs for WebSocket errors:**
   ```bash
   docker compose logs api | grep -i websocket
   ```

4. **Ensure container is running:**
   ```bash
   docker ps | grep testit
   ```

### Issue 3: CORS Errors in Browser Console

**Symptoms:**
- Browser console shows: "Access to fetch at ... has been blocked by CORS policy"
- Network requests fail with CORS errors

**Solutions:**

1. **Verify CORS middleware is configured:**
   - The API should have `allow_origins=["*"]` for development
   - Check `app/main.py` has CORSMiddleware properly configured

2. **Clear browser cache:**
   - Hard refresh: Ctrl+Shift+R (Windows/Linux) or Cmd+Shift+R (macOS)
   - Or clear browser cache completely

3. **Check request origin:**
   - Frontend should be accessing API from `http://localhost:3000` → `http://localhost:8000`
   - Not from `file://` or a different origin

### Issue 4: Frontend Shows Wrong API URL

**Symptoms:**
- Frontend header shows unexpected API URL
- Requests go to wrong endpoint

**Solutions:**

1. **Check environment variable:**
   ```bash
   docker compose exec frontend env | grep REACT_APP_API_URL
   ```
   Should show: `REACT_APP_API_URL=http://localhost:8000`

2. **Rebuild frontend with correct environment:**
   ```bash
   docker compose down
   docker compose up --build frontend
   ```

3. **For local development (not using Docker):**
   Create `frontend/.env`:
   ```
   REACT_APP_API_URL=http://localhost:8000
   ```

### Issue 5: Services Can't Communicate

**Symptoms:**
- API can't connect to Redis
- Celery worker can't connect to Redis
- Services timeout when trying to communicate

**Solutions:**

1. **Check Docker network:**
   ```bash
   docker network ls
   docker network inspect testit_default
   ```

2. **Verify all services are on same network:**
   ```bash
   docker compose config | grep -A 5 networks
   ```

3. **Restart all services:**
   ```bash
   docker compose down
   docker compose up --build
   ```

## Network Architecture

### Port Mapping

- **3000** → Frontend (React app)
- **8000** → Backend API (FastAPI)
- **6379** → Redis

### Service Communication

#### Browser → Backend
- Browser makes HTTP requests to `http://localhost:8000`
- Browser makes WebSocket connections to `ws://localhost:8000/api/terminal/{session_id}`
- This works because Docker publishes port 8000 to localhost

#### Backend → Redis
- Backend uses `redis://redis:6379/0` (service name `redis`)
- This works via Docker's internal network

#### Celery → Redis
- Celery uses `redis://redis:6379/0` (service name `redis`)
- This works via Docker's internal network

## Debugging Commands

### View all logs
```bash
docker compose logs -f
```

### View specific service logs
```bash
docker compose logs -f api
docker compose logs -f frontend
docker compose logs -f celery-worker
```

### Test API endpoints
```bash
# Health check
curl http://localhost:8000/health

# API root
curl http://localhost:8000/

# Submit repository (example)
curl -X POST http://localhost:8000/api/submit \
  -H "Content-Type: application/json" \
  -d '{"repo_url": "https://github.com/docker/welcome-to-docker"}'
```

### Check WebSocket with wscat
```bash
npm install -g wscat
wscat -c ws://localhost:8000/api/terminal/{session_id}
```

## Browser Developer Tools

### Check Network Tab
1. Open browser DevTools (F12)
2. Go to Network tab
3. Try submitting a repository
4. Look for:
   - Failed requests (red)
   - CORS errors
   - 404 or 500 errors

### Check Console Tab
1. Open browser DevTools (F12)
2. Go to Console tab
3. Look for:
   - JavaScript errors
   - CORS errors
   - WebSocket connection errors

## Still Having Issues?

1. **Completely reset the environment:**
   ```bash
   docker compose down -v
   docker system prune -f
   docker compose up --build
   ```

2. **Check Docker Desktop is running:**
   - Ensure Docker Desktop is running
   - Check Docker has enough resources (4GB RAM minimum)

3. **Verify Docker Compose version:**
   ```bash
   docker compose version
   ```
   Should be v2.0 or higher

4. **Check firewall settings:**
   - Ensure ports 3000, 8000, and 6379 are not blocked
   - Disable firewall temporarily for testing

5. **Check logs for specific errors:**
   ```bash
   docker compose logs | grep -i error
   docker compose logs | grep -i cors
   docker compose logs | grep -i websocket
   ```

## Production Considerations

For production deployments, update CORS settings:

1. **In `app/main.py`, change:**
   ```python
   allow_origins=["*"]  # Development only
   ```
   to:
   ```python
   allow_origins=[
       "https://your-frontend-domain.com",
       "https://www.your-frontend-domain.com"
   ]
   ```

2. **Use environment variables:**
   ```python
   allow_origins=os.getenv("ALLOWED_ORIGINS", "").split(",")
   ```

3. **Enable HTTPS/WSS:**
   - Use TLS certificates
   - Update WebSocket URLs to use `wss://`
   - Configure reverse proxy (nginx, Traefik)
