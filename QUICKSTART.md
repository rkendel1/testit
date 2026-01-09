# Quick Start Guide

Get TestIt running in under 5 minutes!

## Prerequisites

- Docker Desktop installed and running
- (Optional) Node.js 18+ for frontend development

## Installation

### Option 1: Docker Compose (Recommended)

1. **Clone the repository**:
```bash
git clone https://github.com/rkendel1/testit.git
cd testit
```

2. **Start the services**:
```bash
docker-compose up --build
```

3. **Wait for services to start** (watch the logs):
   - ✓ Redis ready
   - ✓ API server running on port 8000
   - ✓ Frontend UI running on port 3000
   - ✓ Celery worker connected

4. **Verify it's working**:
```bash
curl http://localhost:8000/health
```

5. **Access the application**:
   - Frontend UI: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

### Option 2: Using Make

```bash
make setup    # Validate your environment
make up       # Start all services
```

## First Test

### Using the API

1. **Submit a test repository**:
```bash
curl -X POST http://localhost:8000/api/submit \
  -H "Content-Type: application/json" \
  -d '{"repo_url": "https://github.com/docker/welcome-to-docker"}'
```

2. **Get the task_id from the response** and check status:
```bash
curl http://localhost:8000/api/status/{task_id}
```

3. **When status is "success", get the session_id** and connect to terminal:
   - Open the API docs: http://localhost:8000/docs
   - Find the WebSocket endpoint
   - Or use the frontend (see below)

### Using the Frontend

With docker-compose running, the frontend is already available at http://localhost:3000.

**If you want to run the frontend separately for development:**

1. **Install frontend dependencies**:
```bash
cd frontend
npm install
```

2. **Start the frontend**:
```bash
npm start
```

3. **Open browser**: http://localhost:3000

**Using the UI:**

1. **Submit a repository**:
   - Enter: `https://github.com/docker/welcome-to-docker`
   - Click "Submit Repository"
   - Wait for build to complete
   - Access the terminal!

2. **Try commands in the terminal**:
```bash
ls -la
pwd
python --version
whoami
```

## Example Repositories

Try these for testing:

1. **Simple Dockerfile**:
   - `https://github.com/docker/welcome-to-docker`

2. **Python Project**:
   - `https://github.com/pallets/flask`

3. **Node.js Project**:
   - `https://github.com/expressjs/express`

## Common Commands

```bash
# Start services
make up

# View logs
make logs

# Stop services
make down

# Clean everything
make clean

# Run API tests
make test
```

## Troubleshooting

### "Connection refused" errors
- Make sure Docker is running: `docker ps`
- Restart services: `make down && make up`

### Build takes too long
- First build can take 5-10 minutes
- Check logs: `docker-compose logs -f celery-worker`

### WebSocket connection fails
- Ensure backend is running
- Check console for errors
- Verify session exists: `curl http://localhost:8000/api/sessions`

### Port already in use
- Stop other services using ports 8000, 6379, or 3000
- Or change ports in docker-compose.yml

## Next Steps

- Read [ARCHITECTURE.md](ARCHITECTURE.md) for system design
- Read [DEVELOPMENT.md](DEVELOPMENT.md) for development guide
- Read [EXAMPLES.md](EXAMPLES.md) for more test cases
- Check out [README.md](README.md) for detailed documentation

## Getting Help

1. Check the logs: `docker-compose logs -f`
2. Visit API docs: http://localhost:8000/docs
3. Review example repositories in EXAMPLES.md
4. Check troubleshooting section in README.md

## What's Happening Behind the Scenes?

When you submit a repository:

1. **Clone**: Git clones your repository
2. **Detect**: Detects language (Python, Node, Java, Go)
3. **Generate**: Creates a Dockerfile if needed
4. **Build**: Builds a Docker image
5. **Run**: Starts an ephemeral container
6. **Connect**: Provides WebSocket terminal access
7. **Cleanup**: Auto-destroys after 60 minutes

## Success!

If you can:
- ✓ Submit a repository via API or frontend
- ✓ See the build complete successfully
- ✓ Connect to the terminal via WebSocket
- ✓ Run commands in the container

Then congratulations! 🎉 TestIt is working!

## Quick Reference

| What | Where |
|------|-------|
| API | http://localhost:8000 |
| API Docs | http://localhost:8000/docs |
| Frontend | http://localhost:3000 |
| Health Check | http://localhost:8000/health |
| Redis | localhost:6379 |

Now go build something amazing! 🚀
