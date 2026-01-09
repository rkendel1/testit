# Frontend-Backend Connection Fix

## Problem
The frontend was unable to reach the backend when running in Docker containers, resulting in:
- 500 Internal Server Error for `/health` endpoint
- 500 Internal Server Error for `/api/submit` endpoint
- Error message: "Could not proxy request /api/submit from 127.0.0.1:3000 to http://localhost:8000 (ECONNREFUSED)"

## Root Cause
The frontend's `package.json` was configured with:
```json
"proxy": "http://localhost:8000"
```

When running in Docker containers:
- The frontend runs in a container named `frontend` (from docker-compose.yml)
- The backend runs in a container named `api` (from docker-compose.yml)
- `localhost` inside the frontend container refers to the container itself, not the backend
- This caused connection refused errors when the frontend tried to proxy requests

## Solution
The fix involves three key changes:

### 1. Created `frontend/src/setupProxy.js`
This file properly configures the HTTP and WebSocket proxy using the Docker service name:

```javascript
const { createProxyMiddleware } = require('http-proxy-middleware');

module.exports = function(app) {
  // Proxy API requests
  app.use(
    '/api',
    createProxyMiddleware({
      target: 'http://api:8000',  // Uses Docker service name 'api'
      changeOrigin: true,
      ws: true,  // Enable WebSocket proxying for terminal
      logLevel: 'debug',
    })
  );

  // Proxy health check
  app.use(
    '/health',
    createProxyMiddleware({
      target: 'http://api:8000',
      changeOrigin: true,
      logLevel: 'debug',
    })
  );
};
```

**Key points:**
- Uses `http://api:8000` instead of `http://localhost:8000`
- `api` is the Docker Compose service name for the backend
- `ws: true` enables WebSocket proxying for the terminal feature
- `changeOrigin: true` updates the Host header to the target URL

### 2. Installed `http-proxy-middleware`
Added as a dev dependency to support the custom proxy configuration:
```bash
npm install --save-dev http-proxy-middleware
```

### 3. Updated CORS Configuration in Backend
Updated `app/main.py` to allow requests from the frontend Docker service:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Frontend dev server on host
        "http://frontend:3000",   # Frontend container in Docker network
        "http://127.0.0.1:3000",  # Localhost variant
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 4. Removed Old Proxy Configuration
Removed the simple proxy line from `package.json` since we now use `setupProxy.js`.

## How Docker Networking Works

In Docker Compose, containers can communicate using service names:

```yaml
services:
  api:        # This is the service name
    ports:
      - "8000:8000"
  
  frontend:   # This is the service name
    ports:
      - "3000:3000"
```

- From the **host machine**: Access via `localhost:3000` or `localhost:8000`
- From **frontend container**: Access backend via `http://api:8000`
- From **api container**: Access frontend via `http://frontend:3000`

## Testing the Fix

### Start the services:
```bash
docker-compose up --build
```

### Verify health check works:
```bash
curl http://localhost:8000/health
```

### Access the frontend:
Open http://localhost:3000 in your browser and:
1. The status should show "✓ Healthy" instead of "✗ Unavailable"
2. Submit a test repository (e.g., `https://github.com/docker/welcome-to-docker`)
3. The submission should succeed without 500 errors
4. When the build completes, the WebSocket terminal should connect successfully

## What This Fixes

✅ HTTP requests from frontend to backend (`/api/*`, `/health`)
✅ WebSocket connections for terminal access (`/api/terminal/{session_id}`)
✅ CORS headers for proper cross-origin communication
✅ Proper Docker networking using service names

## Files Changed

1. `frontend/src/setupProxy.js` - Created (new proxy configuration)
2. `frontend/package.json` - Updated (removed old proxy, added http-proxy-middleware)
3. `frontend/package-lock.json` - Updated (dependency lock file)
4. `app/main.py` - Updated (CORS configuration)

## Additional Notes

- The simple `"proxy"` field in package.json doesn't support WebSocket proxying well
- `setupProxy.js` is the React-recommended way to configure custom proxies
- The fix maintains compatibility with both Docker Compose and local development
- No changes needed to docker-compose.yml or Dockerfiles
