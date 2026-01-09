# Docker API Connection Fix

## Problem
The application was experiencing connection issues with the following error:
```
Error while fetching server API version: Not supported URL scheme http+docker
```

This caused the `/health` endpoint to fail with a 503 error and prevented all Docker operations from working.

## Root Cause
The issue was caused by a bug in docker-py version 7.0.0 that incorrectly parses the `DOCKER_HOST` environment variable when running inside a Docker container. The bug affects the URL scheme parsing logic in the Docker client initialization.

## Solution
Downgraded the `docker` package from version 7.0.0 to 6.1.3 in `requirements.txt`.

### Changes Made
1. **requirements.txt**: Changed `docker==7.0.0` to `docker==6.1.3`
2. **app/docker_utils.py**: Updated comment to document the version constraint

## Verification
- ✅ Docker client initialization tested and working
- ✅ No security vulnerabilities found in docker 6.1.3
- ✅ Code review passed with no issues
- ✅ CodeQL security scan passed with no alerts

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

## References
- docker-py issue tracker: Known issues with version 7.0.0 URL parsing
- Version 6.1.3 is stable and widely used in production
