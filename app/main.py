from fastapi import FastAPI, HTTPException, WebSocket
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from celery.result import AsyncResult
from typing import List
import logging

from app.models import (
    SubmitRepoRequest, 
    SubmitRepoResponse, 
    BuildStatusResponse,
    SessionInfo,
    BuildStatus,
    SessionStatus,
    LanguageType
)
from app.celery_app import celery_app
from app.tasks import process_repository, cleanup_session_task
from app.session_manager import SessionManager
from app.docker_orchestrator import DockerOrchestrator
from app.terminal_manager import TerminalManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="TestIt - Ephemeral Container Build System",
    description="Backend API for building and running ephemeral containers from GitHub repositories",
    version="1.0.0"
)

# Add CORS middleware for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend dev server; restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize terminal manager
terminal_manager = TerminalManager()


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "TestIt API - Ephemeral Container Build System",
        "version": "1.0.0",
        "description": "Submit GitHub repos, get ephemeral containers with browser terminal access",
        "endpoints": {
            "submit": "POST /api/submit",
            "status": "GET /api/status/{task_id}",
            "sessions": "GET /api/sessions",
            "session": "GET /api/sessions/{session_id}",
            "terminal": "WS /api/terminal/{session_id}",
            "stop_session": "DELETE /api/sessions/{session_id}"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check Redis connection
        session_manager = SessionManager()
        session_manager.redis_client.ping()
        
        # Check Docker connection
        orchestrator = DockerOrchestrator()
        orchestrator.client.ping()
        
        return {"status": "healthy"}
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")


@app.post("/api/submit", response_model=SubmitRepoResponse)
async def submit_repository(request: SubmitRepoRequest):
    """
    Submit a GitHub repository for processing
    
    This endpoint:
    1. Validates the repository URL
    2. Queues a task to clone, analyze, build, and run the repository
    3. Returns a task ID for status tracking
    """
    try:
        logger.info(f"Received repository submission: {request.repo_url}")
        
        # Queue the processing task
        task = process_repository.delay(str(request.repo_url))
        
        logger.info(f"Task queued: {task.id}")
        
        return SubmitRepoResponse(
            task_id=task.id,
            status=BuildStatus.PENDING,
            message="Repository queued for processing"
        )
    
    except Exception as e:
        logger.error(f"Error submitting repository: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to queue repository: {str(e)}")


@app.get("/api/status/{task_id}", response_model=BuildStatusResponse)
async def get_build_status(task_id: str):
    """
    Get the status of a build task
    
    Returns:
    - Task status (pending, building, success, failed)
    - Build logs
    - Session information if successful
    """
    try:
        task_result = AsyncResult(task_id, app=celery_app)
        
        if task_result.state == 'PENDING':
            return BuildStatusResponse(
                task_id=task_id,
                status=BuildStatus.PENDING,
                logs="Task is waiting in queue"
            )
        
        elif task_result.state == 'PROGRESS':
            meta = task_result.info or {}
            return BuildStatusResponse(
                task_id=task_id,
                status=BuildStatus.BUILDING,
                logs=meta.get('message', 'Building...')
            )
        
        elif task_result.state == 'SUCCESS':
            result = task_result.result
            
            return BuildStatusResponse(
                task_id=task_id,
                status=BuildStatus(result.get('status', 'success')),
                language=LanguageType(result.get('language')) if result.get('language') else None,
                dependencies=result.get('dependencies'),
                logs=result.get('logs'),
                session_id=result.get('session_id'),
                container_id=result.get('container_id'),
                access_url=result.get('access_url')
            )
        
        elif task_result.state == 'FAILURE':
            return BuildStatusResponse(
                task_id=task_id,
                status=BuildStatus.FAILED,
                logs=f"Task failed: {str(task_result.info)}"
            )
        
        else:
            return BuildStatusResponse(
                task_id=task_id,
                status=BuildStatus.BUILDING,
                logs=f"Task state: {task_result.state}"
            )
    
    except Exception as e:
        logger.error(f"Error getting task status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get task status: {str(e)}")


@app.get("/api/sessions", response_model=List[SessionInfo])
async def list_sessions():
    """
    List all active sessions
    """
    try:
        session_manager = SessionManager()
        sessions = session_manager.get_all_active_sessions()
        
        return [
            SessionInfo(
                session_id=s["session_id"],
                container_id=s["container_id"],
                status=SessionStatus(s["status"]),
                language=LanguageType(s["language"]),
                created_at=s["created_at"],
                expires_at=s["expires_at"],
                access_url=f"/api/sessions/{s['session_id']}"
            )
            for s in sessions
        ]
    
    except Exception as e:
        logger.error(f"Error listing sessions: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to list sessions: {str(e)}")


@app.get("/api/sessions/{session_id}", response_model=SessionInfo)
async def get_session(session_id: str):
    """
    Get information about a specific session
    """
    try:
        session_manager = SessionManager()
        session = session_manager.get_session(session_id)
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return SessionInfo(
            session_id=session["session_id"],
            container_id=session["container_id"],
            status=SessionStatus(session["status"]),
            language=LanguageType(session["language"]),
            created_at=session["created_at"],
            expires_at=session["expires_at"],
            access_url=f"/api/sessions/{session['session_id']}"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting session: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get session: {str(e)}")


@app.delete("/api/sessions/{session_id}")
async def stop_session(session_id: str):
    """
    Stop and cleanup a session
    """
    try:
        session_manager = SessionManager()
        session = session_manager.get_session(session_id)
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        container_id = session["container_id"]
        
        # Queue cleanup task directly (not using BackgroundTasks)
        cleanup_session_task.delay(session_id, container_id)
        
        return {
            "message": "Session cleanup initiated",
            "session_id": session_id
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error stopping session: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to stop session: {str(e)}")


@app.post("/api/cleanup")
async def trigger_cleanup():
    """
    Manually trigger cleanup of expired sessions
    (Normally this runs periodically)
    """
    try:
        from app.tasks import periodic_cleanup_task
        task = periodic_cleanup_task.delay()
        
        return {
            "message": "Cleanup task initiated",
            "task_id": task.id
        }
    
    except Exception as e:
        logger.error(f"Error triggering cleanup: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to trigger cleanup: {str(e)}")


@app.websocket("/api/terminal/{session_id}")
async def terminal_websocket(websocket: WebSocket, session_id: str):
    """
    WebSocket endpoint for terminal access to a container
    
    Provides xterm.js compatible WebSocket terminal access
    """
    logger.info(f"WebSocket connection request for session: {session_id}")
    
    try:
        # Get session to verify it exists and get container ID
        session_manager = SessionManager()
        session = session_manager.get_session(session_id)
        
        if not session:
            logger.warning(f"Session not found: {session_id}")
            await websocket.accept()
            await websocket.send_text("Error: Session not found\r\n")
            await websocket.close()
            return
        
        container_id = session["container_id"]
        
        # Verify container is running
        orchestrator = DockerOrchestrator()
        exists, status = orchestrator.get_container_status(container_id)
        
        if not exists or status != "running":
            logger.warning(f"Container not running: {container_id}, status: {status}")
            await websocket.accept()
            await websocket.send_text(f"Error: Container is not running (status: {status})\r\n")
            await websocket.close()
            return
        
        # Handle the terminal session
        logger.info(f"Starting terminal session for {session_id} (container: {container_id})")
        await terminal_manager.handle_terminal_session(websocket, container_id)
        
    except Exception as e:
        logger.error(f"Error in terminal WebSocket: {e}", exc_info=True)
        try:
            await websocket.accept()
            await websocket.send_text(f"Error: {str(e)}\r\n")
            await websocket.close()
        except:
            pass


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
