# Development Guide

This guide helps developers set up and work on the TestIt project locally.

## Local Development Setup

### Backend Development

1. **Create virtual environment**:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

3. **Start Redis** (in separate terminal):
```bash
docker run -d -p 6379:6379 redis:7-alpine
```

4. **Start Celery worker** (in separate terminal):
```bash
celery -A app.celery_app worker --loglevel=info
```

5. **Start Celery beat for periodic tasks** (in separate terminal):
```bash
celery -A app.celery_app beat --loglevel=info
```

6. **Start FastAPI server**:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

7. **Access API documentation**: http://localhost:8000/docs

### Frontend Development

1. **Navigate to frontend**:
```bash
cd frontend
```

2. **Install dependencies**:
```bash
npm install
```

3. **Start development server**:
```bash
npm start
```

4. **Access frontend**: http://localhost:3000

## Code Structure

### Backend (`/app`)

- **main.py**: FastAPI application, routes, WebSocket endpoints
- **celery_app.py**: Celery configuration and beat schedule
- **config.py**: Settings management with pydantic-settings
- **models.py**: Pydantic models for request/response
- **tasks.py**: Celery tasks for async processing
- **language_detector.py**: Language and dependency detection
- **dockerfile_generator.py**: Dynamic Dockerfile generation
- **docker_orchestrator.py**: Docker client operations
- **session_manager.py**: Redis-based session management
- **terminal_manager.py**: WebSocket terminal handler

### Frontend (`/frontend/src`)

- **App.js**: Main application component
- **Terminal.js**: xterm.js terminal component
- **App.css**: Main styles
- **Terminal.css**: Terminal-specific styles

## Testing

### Manual API Testing

Use the included test script:
```bash
./test_api.sh
```

Or use curl:
```bash
# Submit repository
curl -X POST http://localhost:8000/api/submit \
  -H "Content-Type: application/json" \
  -d '{"repo_url": "https://github.com/docker/welcome-to-docker"}'

# Check status
curl http://localhost:8000/api/status/{task_id}

# List sessions
curl http://localhost:8000/api/sessions
```

### Testing WebSocket Terminal

1. Submit a repository and wait for success
2. Use browser DevTools to test WebSocket:
```javascript
const ws = new WebSocket('ws://localhost:8000/api/terminal/{session_id}');
ws.onmessage = (e) => console.log(e.data);
ws.send('ls -la\n');
```

### Testing with Frontend

1. Start backend and frontend
2. Submit a test repository
3. Monitor build progress
4. Access terminal when ready
5. Execute commands and verify output

## Common Development Tasks

### Adding a New Language

1. Update `LanguageType` enum in `models.py`
2. Add detection logic in `language_detector.py`:
   - Add file patterns to `LANGUAGE_PATTERNS`
   - Implement `_detect_<language>_deps()` method
3. Add Dockerfile template in `dockerfile_generator.py`:
   - Implement `_generate_<language>_dockerfile()` method
4. Update documentation

### Adding a New API Endpoint

1. Define Pydantic models in `models.py`
2. Add route in `main.py`
3. Implement business logic (may require new task in `tasks.py`)
4. Update API documentation in README
5. Test with curl or frontend

### Modifying Container Behavior

1. Update `docker_orchestrator.py` for build/run logic
2. Adjust resource limits in `config.py`
3. Test with sample repositories

## Debugging

### Backend Debugging

Enable debug logs:
```python
# In main.py
logging.basicConfig(level=logging.DEBUG)
```

### Celery Task Debugging

Monitor Celery:
```bash
celery -A app.celery_app worker --loglevel=debug
```

Check task status:
```bash
celery -A app.celery_app inspect active
celery -A app.celery_app inspect registered
```

### Docker Debugging

List containers:
```bash
docker ps -a --filter "label=managed_by=testit"
```

Check container logs:
```bash
docker logs {container_id}
```

Exec into container:
```bash
docker exec -it {container_id} /bin/bash
```

### Redis Debugging

Connect to Redis:
```bash
docker exec -it {redis_container} redis-cli
```

Check keys:
```redis
KEYS session:*
GET session:{session_id}
SMEMBERS sessions:active
```

## Performance Considerations

- **Build timeout**: Default 5 minutes (configurable)
- **Session timeout**: Default 60 minutes (configurable)
- **Container limits**: 2 CPU cores, 2GB RAM (configurable)
- **Cleanup interval**: Every 5 minutes (configurable)

## Security Notes

- Never commit `.env` file with secrets
- Be cautious mounting Docker socket in production
- Update CORS origins for production
- Consider adding authentication for production use
- Review container security settings

## Troubleshooting

### "Docker socket permission denied"
```bash
sudo usermod -aG docker $USER
# Then log out and back in
```

### "Redis connection refused"
```bash
# Check if Redis is running
docker ps | grep redis

# Start Redis if not running
docker run -d -p 6379:6379 redis:7-alpine
```

### "Port already in use"
```bash
# Find process using port
lsof -i :8000  # or :3000 for frontend

# Kill process or change port in config
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Celery Documentation](https://docs.celeryproject.org/)
- [Docker SDK for Python](https://docker-py.readthedocs.io/)
- [xterm.js Documentation](https://xtermjs.org/)
- [React Documentation](https://react.dev/)
