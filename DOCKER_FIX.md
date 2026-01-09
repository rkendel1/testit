# Docker API Connection Fix

## Problem
The application was experiencing connection issues with the following error:
```
Error while fetching server API version: Not supported URL scheme http+docker
```

This caused the `/health` endpoint to fail with a 503 error and prevented all Docker operations from working.

## Root Cause
The issue was caused by an incompatibility between `docker-py 6.1.3` and `urllib3 2.0+`. The docker-py library version 6.x does not support urllib3 2.0, which introduced breaking changes to URL handling. When docker-py 6.x attempts to use urllib3 2.x, it generates the error: `Not supported URL scheme http+docker`.

This incompatibility affects all Docker operations including:
- Docker client initialization
- Health check endpoints
- Container building and running
- WebSocket connections

## Solution
Upgraded the docker library from version 6.1.3 to 7.1.0, which properly supports urllib3 2.0+.

### Changes Made
1. **requirements.txt**: Upgraded `docker==6.1.3` to `docker==7.1.0`
2. **app/docker_utils.py**: 
   - Existing logic continues to work correctly with docker 7.1.0
   - Detects unix socket URLs in DOCKER_HOST
   - Uses explicit `DockerClient(base_url=...)` for unix sockets
   - Uses `docker.from_env()` for other cases (maintains TLS support)

## Verification
- ✅ Docker client initialization tested and working with unix sockets
- ✅ Docker client initialization tested and working without DOCKER_HOST
- ✅ No security vulnerabilities found (CodeQL scan: 0 alerts)
- ✅ Code review passed with no issues
- ✅ Maintains TLS support for TCP connections

## Impact
This fix resolves:
- Health check endpoint failures
- WebSocket connection rejections
- Build failures with "Error while fetching server API version"
- All Docker operations that depend on the Docker client

## Next Steps
After deploying this fix:
1. Rebuild the Docker images: `docker compose build`
2. Restart the services: `docker compose up -d`
3. Verify the health endpoint: `curl http://localhost:8000/health`
4. Test repository submission and build process

## Technical Details
The fix is minimal and surgical:
- Only affects Docker client initialization
- Preserves TLS handling for TCP connections
- Works in both containerized and non-containerized environments
- No breaking changes to the API or functionality
