# TestIt - System Architecture

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         User's Browser                          │
│                                                                 │
│  ┌──────────────────┐        ┌────────────────────────────┐   │
│  │  React Frontend  │        │  WebSocket Terminal        │   │
│  │  (Port 3000)     │◄──────►│  (xterm.js)                │   │
│  └────────┬─────────┘        └────────────────────────────┘   │
└───────────┼──────────────────────────────────────────────────────┘
            │ HTTP/REST
            │ WebSocket
            ▼
┌─────────────────────────────────────────────────────────────────┐
│                      FastAPI Backend                            │
│                       (Port 8000)                               │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  REST API Endpoints                                       │  │
│  │  • POST /api/submit                                       │  │
│  │  • GET  /api/status/{task_id}                            │  │
│  │  • GET  /api/sessions                                     │  │
│  │  • DELETE /api/sessions/{session_id}                      │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  WebSocket Endpoint                                       │  │
│  │  • WS /api/terminal/{session_id}                         │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────┬────────────────────────────┬────────────────────────────┘
         │                            │
         │ Queue Tasks                │ WebSocket → Docker Exec
         ▼                            ▼
┌────────────────────┐      ┌────────────────────────────────────┐
│  Celery + Redis    │      │   Terminal Manager                 │
│  (Port 6379)       │      │   • WebSocket Handler              │
│                    │      │   • Docker Exec Integration        │
│  ┌──────────────┐  │      └────────────────────────────────────┘
│  │ Task Queue   │  │                     │
│  │              │  │                     │ Docker API
│  └──────┬───────┘  │                     ▼
│         │          │      ┌────────────────────────────────────┐
│  ┌──────▼───────┐  │      │   Docker Orchestrator             │
│  │Celery Worker │  │      │   • Build images                   │
│  │              │  │      │   • Run containers                 │
│  └──────┬───────┘  │      │   • Manage lifecycle               │
│         │          │      └────────────────────────────────────┘
│  ┌──────▼───────┐  │                     │
│  │ Celery Beat  │  │                     │ Docker API
│  │ (Scheduler)  │  │                     ▼
│  └──────────────┘  │      ┌────────────────────────────────────┐
└────────┬────────────┘      │   Docker Daemon                   │
         │                   │                                    │
         │ Store Sessions    │  ┌──────────────────────────────┐ │
         ▼                   │  │  Ephemeral Container         │ │
┌────────────────────┐       │  │  • Built from repo           │ │
│  Session Manager   │       │  │  • Resource limits           │ │
│  (Redis)           │       │  │  • Auto-destroy timeout      │ │
│                    │       │  │  • Terminal access           │ │
│  • Session data    │       │  └──────────────────────────────┘ │
│  • Expiration      │       └────────────────────────────────────┘
│  • Cleanup         │
└────────────────────┘
```

## Component Breakdown

### 1. Frontend Layer (React + xterm.js)
- **Technology**: React 18
- **Purpose**: User interface for submitting repos and accessing terminals
- **Key Features**:
  - Repository submission form
  - Build status polling
  - WebSocket terminal integration with xterm.js
  - Session management UI

### 2. API Layer (FastAPI)
- **Technology**: FastAPI + Uvicorn
- **Purpose**: REST API and WebSocket gateway
- **Endpoints**:
  - Repository submission
  - Build status queries
  - Session management
  - WebSocket terminal connections
- **Features**:
  - CORS middleware for frontend
  - Async/await support
  - Auto-generated OpenAPI docs

### 3. Task Queue (Celery + Redis)
- **Technology**: Celery 5 + Redis 7
- **Purpose**: Async task processing and scheduling
- **Tasks**:
  - `process_repository`: Main build and run workflow
  - `cleanup_session_task`: Clean up individual sessions
  - `periodic_cleanup_task`: Scheduled cleanup of expired sessions
- **Beat Schedule**: Runs cleanup every 5 minutes

### 4. Core Modules

#### Language Detector
- Detects programming language from repository structure
- Supports: Python, Node.js, Java, Go
- Extracts dependency information
- Checks for existing Dockerfiles

#### Dockerfile Generator
- Creates language-specific Dockerfiles
- Handles different build tools (pip, npm, maven, gradle, go mod)
- Multi-stage builds for compiled languages (Java, Go)

#### Docker Orchestrator
- Manages Docker client operations
- Builds images from generated Dockerfiles
- Runs containers with resource limits
- Cleans up old containers

#### Session Manager
- Stores session data in Redis
- Tracks container mappings
- Handles expiration and timeouts
- Manages session lifecycle

#### Terminal Manager
- Handles WebSocket connections
- Connects to container via Docker exec
- Bidirectional data streaming
- Terminal session lifecycle

### 5. Storage Layer (Redis)
- **Purpose**: 
  - Celery broker and result backend
  - Session data storage
- **Data Structures**:
  - `session:{session_id}`: Session metadata (hash)
  - `sessions:active`: Set of active session IDs
  - Celery internal queues

### 6. Container Runtime (Docker)
- **Purpose**: Run ephemeral user containers
- **Configuration**:
  - Memory limit: 2GB
  - CPU limit: 2 cores
  - Auto-remove: No (managed by session cleanup)
  - Labels: `managed_by=testit`
- **Network**: Default bridge network
- **Ports**: Exposed based on language (8000, 3000, 8080, etc.)

## Data Flow

### 1. Repository Submission Flow
```
User submits URL
    ↓
Frontend POST /api/submit
    ↓
FastAPI validates and queues task
    ↓
Returns task_id to frontend
    ↓
Frontend polls GET /api/status/{task_id}
```

### 2. Build & Run Flow
```
Celery picks up task
    ↓
Clone repository (git clone)
    ↓
Detect language and dependencies
    ↓
Check for Dockerfile or generate one
    ↓
Build Docker image (docker build)
    ↓
Run container (docker run)
    ↓
Create session in Redis
    ↓
Return session_id and container_id
```

### 3. Terminal Access Flow
```
User clicks "Connect to Terminal"
    ↓
Frontend opens WebSocket to /api/terminal/{session_id}
    ↓
Backend validates session and container
    ↓
Terminal Manager creates Docker exec session
    ↓
Bidirectional data flow: Browser ↔ WebSocket ↔ Docker Exec ↔ Container Shell
```

### 4. Session Cleanup Flow
```
Celery Beat runs periodic_cleanup_task
    ↓
Session Manager checks for expired sessions
    ↓
For each expired session:
    ↓
    Stop and remove container
    ↓
    Delete session from Redis
```

## Security Considerations

1. **Container Isolation**: Each user gets isolated container
2. **Resource Limits**: CPU and memory limits prevent resource exhaustion
3. **Session Timeout**: Auto-destroy prevents long-running containers
4. **Docker Socket**: Mounted (⚠️ requires careful handling in production)
5. **Network**: Containers use default bridge (consider custom networks)

## Scalability

### Current PoC Limitations
- Single Docker host
- No load balancing
- No container orchestration (beyond Docker)
- Limited concurrent builds

### Future Scaling Options
1. **Kubernetes**: Replace Docker with K8s pods
2. **Load Balancing**: Multiple API instances behind LB
3. **Worker Scaling**: More Celery workers
4. **Build Caching**: Cache Docker layers
5. **Storage**: Persistent storage for artifacts

## Performance Characteristics

- **Build Time**: 30s - 5min (depends on repo)
- **Session Timeout**: 60 minutes (configurable)
- **Cleanup Interval**: 5 minutes
- **Concurrent Sessions**: Limited by Docker host resources
- **Memory per Container**: Up to 2GB
- **CPU per Container**: Up to 2 cores

## Monitoring & Observability

### Current Logging
- FastAPI logs: Request/response
- Celery logs: Task execution
- Docker logs: Container output
- Application logs: Business logic

### Future Enhancements
- Metrics (Prometheus)
- Distributed tracing
- Health checks
- Alerting

## Technology Stack Summary

| Layer | Technology | Version |
|-------|-----------|---------|
| Frontend | React | 18.2 |
| Terminal | xterm.js | 5.3 |
| API | FastAPI | 0.109 |
| Web Server | Uvicorn | 0.27 |
| Task Queue | Celery | 5.3 |
| Broker/Cache | Redis | 7.0 |
| Container Runtime | Docker | Latest |
| Language | Python | 3.11 |
| Language (Frontend) | JavaScript | ES6+ |
