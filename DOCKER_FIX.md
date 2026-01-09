# Docker API Connection Fix

## Problem
The application was experiencing connection issues with the following error:
```
Error while fetching server API version: Not supported URL scheme http+docker
```

This caused the `/health` endpoint to fail with a 503 error and prevented all Docker operations from working.

## Root Cause
The issue was caused by a bug in docker-py's URL parsing logic when handling unix socket URLs in the DOCKER_HOST environment variable. The `docker.from_env()` method was not correctly parsing `unix:///var/run/docker.sock`, leading to a malformed URL scheme.

## Solution
Modified the Docker client initialization in `app/docker_utils.py` to:
1. Check if DOCKER_HOST is set and is a unix socket URL (`unix://`)
2. For unix sockets, explicitly pass the URL to `docker.DockerClient(base_url=docker_host)`
3. For all other cases (TCP connections or no DOCKER_HOST), use `docker.from_env()` which properly handles TLS

### Changes Made
1. **requirements.txt**: Using `docker==6.1.3` (stable version)
2. **app/docker_utils.py**: 
   - Added logic to detect unix socket URLs in DOCKER_HOST
   - Bypass `docker.from_env()` only for unix sockets
   - Maintain TLS support for TCP connections

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
