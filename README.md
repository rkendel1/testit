# TestIt - Ephemeral Container Build System

A proof-of-concept platform that allows users to submit GitHub repository links and automatically builds and runs them in ephemeral Docker containers with browser-based terminal access.

## 🎯 Features

- **Automatic Language Detection**: Detects Python, Node.js, Java, and Go projects
- **Smart Dockerfile Generation**: Automatically generates Dockerfiles if not present
- **Ephemeral Containers**: Containers auto-destroy after 60 minutes
- **Browser Terminal**: Access containers via xterm.js WebSocket terminal
- **Resource Management**: Enforces CPU (2 cores) and memory (2GB) limits
- **Queue-Based Processing**: Uses Celery + Redis for scalable task management
- **Session Management**: Tracks and manages container sessions

## 🏗️ Architecture

```
[React Frontend with xterm.js] 
         ↓
[FastAPI REST API + WebSocket] 
         ↓
[Celery Job Queue] ← Redis
         ↓
[Docker Build & Run] 
         ↓
[Ephemeral Container with Terminal Access]
         ↓
[Auto-Destroy after Timeout]
```

## 📋 Supported Repositories

### ✅ Fully Supported
- Projects with existing Dockerfile
- Python projects (requirements.txt, setup.py, pyproject.toml)
- Node.js projects (package.json)
- Java projects (pom.xml, build.gradle)
- Go projects (go.mod)

### ❌ Not Supported (v1)
- Windows-only projects
- Multi-service orchestration (docker-compose with multiple services)
- GPU-heavy ML projects
- Projects requiring external services

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose installed
- Git
- Node.js 18+ (for frontend development)
- Python 3.11+ (for backend development)

### Running with Docker Compose (Recommended)

1. Clone the repository:
```bash
git clone https://github.com/rkendel1/testit.git
cd testit
```

2. Start the services:
```bash
docker-compose up --build
```

3. Access the application:
- Frontend UI: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

### Running Frontend Separately (Development)

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Start the development server:
```bash
npm start
```

4. Open http://localhost:3000 in your browser

### Running Backend Locally (Development)

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Start Redis:
```bash
docker run -d -p 6379:6379 redis:7-alpine
```

4. Start the Celery worker:
```bash
celery -A app.celery_app worker --loglevel=info
```

5. Start the FastAPI server:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 📖 API Documentation

### Submit Repository
```http
POST /api/submit
Content-Type: application/json

{
  "repo_url": "https://github.com/username/repo"
}
```

Response:
```json
{
  "task_id": "uuid",
  "status": "pending",
  "message": "Repository queued for processing"
}
```

### Check Build Status
```http
GET /api/status/{task_id}
```

Response:
```json
{
  "task_id": "uuid",
  "status": "success",
  "language": "python",
  "session_id": "session-uuid",
  "container_id": "container-id",
  "access_url": "/api/sessions/session-uuid",
  "logs": "Build logs..."
}
```

### Connect to Terminal (WebSocket)
```
WS /api/terminal/{session_id}
```

### List Active Sessions
```http
GET /api/sessions
```

### Stop Session
```http
DELETE /api/sessions/{session_id}
```

## 🔧 Configuration

Environment variables (create `.env` file):

```bash
# Redis
REDIS_URL=redis://localhost:6379/0

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Docker
DOCKER_SOCKET=unix://var/run/docker.sock

# Session Settings
SESSION_TIMEOUT_MINUTES=60
SESSION_CLEANUP_INTERVAL_MINUTES=5

# Container Limits
CONTAINER_MEMORY_LIMIT=2g
CONTAINER_CPU_LIMIT=2.0
CONTAINER_CPU_COUNT=2

# Build Settings
BUILD_TIMEOUT_SECONDS=300
```

## 🧪 Testing

### Test with Sample Repositories

1. **Python Project with Dockerfile**:
```
https://github.com/docker/welcome-to-docker
```

2. **Simple Python Project**:
```
https://github.com/pallets/flask
```

3. **Node.js Project**:
```
https://github.com/vercel/next.js
```

### Manual Testing Flow

1. Submit a repository URL via the frontend
2. Monitor build progress
3. Once successful, access the terminal
4. Run commands in the container
5. Stop the session or wait for auto-destroy

## 🔒 Security Considerations

### ⚠️ Production Security Warnings

1. **Docker Socket Mount**: The current implementation mounts `/var/run/docker.sock` into containers, which provides root-level access to the host Docker daemon. This is acceptable for PoC and development but **should NOT be used in production**. For production:
   - Use Docker-in-Docker (DinD) with proper isolation
   - Consider alternative container runtimes (Podman, gVisor)
   - Implement proper network isolation
   - Use Kubernetes with proper RBAC instead of direct Docker

2. **Resource Limits**: Containers run with CPU and memory limits to prevent resource exhaustion

3. **Session Timeout**: Sessions automatically expire after timeout to prevent long-running containers

4. **CORS Configuration**: CORS is configured with `allow_origins=["*"]` for development. Update this to specific origins in production

5. **No Authentication**: The current PoC has no authentication. Add authentication before production deployment

6. **Container Security**: 
   - Containers run as root (should use non-root users in production)
   - No AppArmor/SELinux profiles configured
   - No network policies implemented

### Recommendations for Production

- Add user authentication and authorization
- Implement rate limiting
- Use proper container orchestration (Kubernetes)
- Add network isolation between containers
- Implement audit logging
- Add vulnerability scanning for user-submitted code
- Use read-only root filesystems
- Implement proper secrets management

## 📝 Project Structure

```
testit/
├── app/
│   ├── main.py                 # FastAPI application
│   ├── celery_app.py           # Celery configuration
│   ├── config.py               # Settings management
│   ├── models.py               # Pydantic models
│   ├── tasks.py                # Celery tasks
│   ├── language_detector.py   # Language detection
│   ├── dockerfile_generator.py # Dockerfile generation
│   ├── docker_orchestrator.py  # Docker operations
│   ├── session_manager.py      # Session management
│   └── terminal_manager.py     # WebSocket terminal
├── frontend/
│   ├── public/
│   └── src/
│       ├── App.js              # Main React component
│       ├── Terminal.js         # xterm.js terminal
│       └── ...
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── README.md
```

## 🛣️ Roadmap

### v1 (Current PoC)
- [x] Basic repository submission
- [x] Language detection (Python, Node, Java, Go)
- [x] Automatic Dockerfile generation
- [x] Docker build and run
- [x] Session management with auto-destroy
- [x] WebSocket terminal access
- [x] React frontend with xterm.js

### v2 (Future)
- [ ] Jupyter notebook support for Python
- [ ] Port forwarding for web applications
- [ ] Artifact export/download
- [ ] User authentication
- [ ] Build caching
- [ ] Support for more languages
- [ ] Kubernetes deployment option

## 🐛 Troubleshooting

### Container fails to build
- Check build logs in the status response
- Verify the repository has dependency files
- Ensure Docker has enough resources

### WebSocket connection fails
- Check that the container is running
- Verify CORS settings
- Ensure WebSocket protocol matches (ws/wss)

### Sessions not cleaning up
- Check Redis connection
- Verify Celery worker is running
- Manually trigger cleanup: `POST /api/cleanup`

## 📄 License

MIT License - See LICENSE file for details

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 👥 Authors

- Initial PoC implementation by GitHub Copilot

## 🙏 Acknowledgments

- FastAPI for the excellent web framework
- xterm.js for browser terminal support
- Docker for containerization
- Celery for task queue management
