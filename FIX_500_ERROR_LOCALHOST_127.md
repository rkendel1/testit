# Fix for 500 Error with localhost/127.0.0.1 Connectivity

## Problem
The frontend was getting a 500 error when trying to connect to the backend API, with the error message:
```
Could not proxy request /api/submit from 127.0.0.1:3000 to http://localhost:8000 (ECONNREFUSED)
```

This occurred because:
1. Users could access the frontend via either `localhost:3000` or `127.0.0.1:3000`
2. The proxy configuration in `setupProxy.js` was hardcoded to `http://api:8000` (Docker service name)
3. When running in Docker, the proxy needs to use the Docker service name (`api`), not `localhost`
4. The CORS configuration already supported `127.0.0.1:3000`, so that wasn't the issue

## Solution
Made the proxy target configurable via environment variables:

### 1. Updated `frontend/src/setupProxy.js`
Changed from hardcoded `http://api:8000` to:
```javascript
const target = process.env.PROXY_TARGET || process.env.REACT_APP_PROXY_TARGET || 'http://api:8000';
```

This allows the proxy target to be configured via:
- `PROXY_TARGET` environment variable (highest priority)
- `REACT_APP_PROXY_TARGET` environment variable (medium priority)  
- Default to `http://api:8000` (Docker service name, lowest priority)

### 2. Updated `docker-compose.yml`
Added the environment variable to the frontend service:
```yaml
environment:
  - REACT_APP_API_URL=http://localhost:8000  # For browser-side requests
  - REACT_APP_PROXY_TARGET=http://api:8000    # For server-side proxy (NEW)
```

### 3. Updated `frontend/.env.example`
Added documentation for the new environment variable:
```
# Backend proxy target (for server-side proxy requests from Node.js)
# When running in Docker, use the Docker service name: http://api:8000
# When running locally outside Docker, use http://localhost:8000 or http://127.0.0.1:8000
REACT_APP_PROXY_TARGET=http://api:8000
```

## How It Works

### In Docker (with docker-compose)
1. Frontend container runs Node.js dev server
2. `setupProxy.js` reads `REACT_APP_PROXY_TARGET=http://api:8000`
3. Proxy forwards requests to the `api` Docker service
4. User's browser can access frontend via `localhost:3000` OR `127.0.0.1:3000` - both work!

### Local Development (outside Docker)
1. Set `REACT_APP_PROXY_TARGET=http://localhost:8000` (or `http://127.0.0.1:8000`)
2. Proxy forwards requests to locally running backend
3. Works with both `localhost` and `127.0.0.1`

## Testing

### With Docker Compose
```bash
docker-compose up --build
```

Then access the frontend via:
- `http://localhost:3000` ✓
- `http://127.0.0.1:3000` ✓

Both should work identically!

### Verify Proxy Configuration
Check the frontend container logs for:
```
[Proxy] Configuring proxy to target: http://api:8000
```

### Test Connectivity
1. Open browser to `http://127.0.0.1:3000`
2. Open DevTools → Network tab
3. Submit a test repository (e.g., `https://github.com/pallets/flask`)
4. Should see successful POST to `/api/submit` with 200/202 response
5. No more ECONNREFUSED errors!

## Files Changed
1. `frontend/src/setupProxy.js` - Made proxy target configurable
2. `docker-compose.yml` - Added `REACT_APP_PROXY_TARGET` environment variable
3. `frontend/.env.example` - Documented the new environment variable

## No Backend Changes Needed
The backend already had CORS configured to accept requests from:
- `http://localhost:3000`
- `http://127.0.0.1:3000` 
- `http://frontend:3000`

So no backend changes were necessary.
