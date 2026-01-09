# API Connection Fix - Testing Instructions

## Problem Fixed
This PR resolves the 504 Gateway Timeout error and API unreachability issues caused by Docker client initialization failing during application startup.

## Root Cause
The API was failing to start because:
1. `TerminalManager()` was initialized at module import time in `app/main.py`
2. This triggered Docker client connection during module import
3. Docker client initialization failed, causing the Uvicorn worker process to crash
4. Result: API never became reachable, leading to 504 errors when frontend tried to connect

## Solution Implemented
Implemented thread-safe lazy initialization pattern:
- Created `app/docker_utils.py` with shared Docker client initialization logic
- Changed `TerminalManager` and `DockerOrchestrator` to use lazy `@property` decorators
- Docker clients are only created when first accessed, not during `__init__`
- All lazy initialization uses double-check locking for thread safety
- Replaced module-level `terminal_manager` with thread-safe `get_terminal_manager()` function

## Files Changed
1. **app/docker_utils.py** (NEW) - Shared Docker client initialization
2. **app/terminal_manager.py** - Thread-safe lazy Docker client property
3. **app/docker_orchestrator.py** - Thread-safe lazy Docker client property
4. **app/main.py** - Thread-safe terminal manager getter

## Testing Instructions

### 1. Stop existing containers
```bash
docker compose down -v
```

### 2. Rebuild and start containers
```bash
docker compose up --build -d
```

### 3. Check API container logs
```bash
docker compose logs api
```

**Expected**: You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [1] using WatchFiles
INFO:     Started server process [X]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

**No longer expected**: The Docker client initialization error should be gone.

### 4. Test health endpoint
```bash
curl http://localhost:8000/health
```

**Expected response**:
```json
{"status":"healthy"}
```

### 5. Test frontend connection
```bash
curl http://localhost:3000/health
```

**Expected response**: Should return the proxied health check from the API, not a proxy error.

### 6. Test in browser
Open http://localhost:3000 in your browser.

**Expected**:
- Page loads successfully
- No 504 Gateway Timeout errors
- "API: http://localhost:8000" shows in the UI
- "Status: Offline" should change to another status (healthy/unhealthy)

## What Changed Technically

### Before (Broken)
```python
# main.py - module level initialization
terminal_manager = TerminalManager()  # ← Fails here during import!

class TerminalManager:
    def __init__(self):
        # Tries to connect to Docker immediately
        self.docker_client = docker.DockerClient(...)  # ← Crash!
```

### After (Fixed)
```python
# main.py - lazy initialization
_terminal_manager = None
_terminal_manager_lock = threading.Lock()

def get_terminal_manager():
    global _terminal_manager
    if _terminal_manager is None:
        with _terminal_manager_lock:
            if _terminal_manager is None:
                _terminal_manager = TerminalManager()  # Safe - no Docker connection yet
    return _terminal_manager

class TerminalManager:
    def __init__(self):
        self._docker_client = None  # No connection yet!
        self._docker_client_lock = threading.Lock()
    
    @property
    def docker_client(self):
        # Only connects when actually needed
        if self._docker_client is None:
            with self._docker_client_lock:
                if self._docker_client is None:
                    self._docker_client = create_docker_client()  # Connect here
        return self._docker_client
```

## Security & Code Quality
- ✅ CodeQL security scan: 0 alerts
- ✅ Thread-safe implementation with double-check locking
- ✅ No code duplication (shared utility function)
- ✅ Minimal changes to codebase
- ✅ Backward compatible

## Troubleshooting

If you still see issues:

1. **Check container status**:
   ```bash
   docker compose ps
   ```
   All containers should show "running" or "Up".

2. **Check all container logs**:
   ```bash
   docker compose logs
   ```

3. **Verify Docker socket mount**:
   ```bash
   docker compose exec api ls -la /var/run/docker.sock
   ```
   Should show the Docker socket file.

4. **Test Docker connection inside API container**:
   ```bash
   docker compose exec api python3 -c "import docker; client = docker.DockerClient(base_url='unix:///var/run/docker.sock'); print(client.ping())"
   ```
   Should print `True`.

## Notes
- This fix ensures the API starts successfully even if Docker connection is temporarily unavailable
- Docker connection is established lazily when actually needed (e.g., when handling terminal WebSocket connections)
- Thread-safe for production use with multiple workers
