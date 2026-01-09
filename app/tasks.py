import os
import logging
import tempfile
import shutil
import subprocess
from typing import Dict
from app.celery_app import celery_app
from app.language_detector import LanguageDetector
from app.dockerfile_generator import DockerfileGenerator
from app.docker_orchestrator import DockerOrchestrator
from app.session_manager import SessionManager
from app.models import LanguageType, BuildStatus

logger = logging.getLogger(__name__)


@celery_app.task(bind=True)
def process_repository(self, repo_url: str) -> Dict:
    """
    Process a GitHub repository:
    1. Clone the repository
    2. Check for Dockerfile or detect language
    3. Generate Dockerfile if needed
    4. Build Docker image
    5. Run container
    6. Create session
    """
    task_id = self.request.id
    temp_dir = None
    
    try:
        logger.info(f"Processing repository: {repo_url}")
        self.update_state(state='PROGRESS', meta={'status': 'cloning', 'message': 'Cloning repository...'})
        
        # Clone repository
        temp_dir = tempfile.mkdtemp(prefix="testit_")
        clone_result = _clone_repository(repo_url, temp_dir)
        
        if not clone_result["success"]:
            return {
                "status": BuildStatus.FAILED.value,
                "message": clone_result["message"],
                "logs": clone_result["message"]
            }
        
        logger.info(f"Repository cloned to: {temp_dir}")
        self.update_state(state='PROGRESS', meta={'status': 'analyzing', 'message': 'Analyzing repository...'})
        
        # Check for existing Dockerfile
        has_dockerfile = LanguageDetector.has_dockerfile(temp_dir)
        dockerfile_content = None
        
        if has_dockerfile:
            logger.info("Found existing Dockerfile")
            with open(os.path.join(temp_dir, "Dockerfile"), 'r') as f:
                dockerfile_content = f.read()
            language = LanguageDetector.detect_language(temp_dir)
        else:
            # Detect language
            language = LanguageDetector.detect_language(temp_dir)
            logger.info(f"Detected language: {language.value}")
            
            if language == LanguageType.UNKNOWN:
                return {
                    "status": BuildStatus.FAILED.value,
                    "message": "Could not detect repository language",
                    "language": language.value,
                    "logs": "No recognizable language or dependency files found"
                }
            
            # Detect dependencies
            dependencies = LanguageDetector.detect_dependencies(temp_dir, language)
            logger.info(f"Detected dependencies: {dependencies}")
            
            # Generate Dockerfile
            self.update_state(state='PROGRESS', meta={'status': 'generating', 'message': 'Generating Dockerfile...'})
            dockerfile_content = DockerfileGenerator.generate_dockerfile(language, temp_dir)
            logger.info("Generated Dockerfile")
        
        # Build Docker image
        self.update_state(state='PROGRESS', meta={'status': 'building', 'message': 'Building Docker image...'})
        
        orchestrator = DockerOrchestrator()
        image_tag = f"testit-{task_id}:latest"
        
        build_success, build_logs = orchestrator.build_image(temp_dir, dockerfile_content, image_tag)
        
        if not build_success:
            return {
                "status": BuildStatus.FAILED.value,
                "message": "Docker build failed",
                "language": language.value,
                "logs": build_logs
            }
        
        logger.info("Docker image built successfully")
        
        # Run container
        self.update_state(state='PROGRESS', meta={'status': 'starting', 'message': 'Starting container...'})
        
        container_name = f"testit-{task_id}"
        run_success, container_id, run_message = orchestrator.run_container(
            image_tag, 
            container_name,
            language
        )
        
        if not run_success:
            return {
                "status": BuildStatus.FAILED.value,
                "message": run_message,
                "language": language.value,
                "logs": build_logs
            }
        
        logger.info(f"Container started: {container_id}")
        
        # Create session
        session_manager = SessionManager()
        session_id = f"session-{task_id}"
        session_data = session_manager.create_session(
            session_id,
            container_id,
            language,
            task_id
        )
        
        # Get dependencies info
        dependencies = LanguageDetector.detect_dependencies(temp_dir, language)
        
        return {
            "status": BuildStatus.SUCCESS.value,
            "message": "Repository processed successfully",
            "language": language.value,
            "dependencies": dependencies,
            "logs": build_logs,
            "session_id": session_id,
            "container_id": container_id,
            "access_url": f"/sessions/{session_id}"
        }
        
    except Exception as e:
        logger.error(f"Error processing repository: {e}", exc_info=True)
        return {
            "status": BuildStatus.FAILED.value,
            "message": f"Unexpected error: {str(e)}",
            "logs": str(e)
        }
    
    finally:
        # Cleanup temporary directory
        if temp_dir and os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir)
                logger.info(f"Cleaned up temp directory: {temp_dir}")
            except Exception as e:
                logger.warning(f"Failed to cleanup temp directory: {e}")


def _clone_repository(repo_url: str, target_dir: str) -> Dict:
    """Clone a git repository"""
    try:
        # Run git clone
        result = subprocess.run(
            ["git", "clone", "--depth", "1", repo_url, target_dir],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0:
            return {"success": True, "message": "Repository cloned successfully"}
        else:
            return {
                "success": False, 
                "message": f"Git clone failed: {result.stderr}"
            }
    except subprocess.TimeoutExpired:
        return {"success": False, "message": "Git clone timeout"}
    except Exception as e:
        return {"success": False, "message": f"Git clone error: {str(e)}"}


@celery_app.task
def cleanup_session_task(session_id: str, container_id: str):
    """Cleanup a session and its container"""
    try:
        logger.info(f"Cleaning up session: {session_id}")
        
        # Stop and remove container
        orchestrator = DockerOrchestrator()
        orchestrator.stop_container(container_id)
        
        # Delete session
        session_manager = SessionManager()
        session_manager.delete_session(session_id)
        
        logger.info(f"Session cleanup completed: {session_id}")
        
    except Exception as e:
        logger.error(f"Error cleaning up session {session_id}: {e}", exc_info=True)


@celery_app.task
def periodic_cleanup_task():
    """Periodic task to cleanup expired sessions"""
    try:
        logger.info("Running periodic cleanup task")
        
        session_manager = SessionManager()
        expired_sessions = session_manager.cleanup_expired_sessions()
        
        # Cleanup each expired session
        for session_id in expired_sessions:
            session = session_manager.get_session(session_id)
            if session:
                container_id = session.get("container_id")
                if container_id:
                    cleanup_session_task.delay(session_id, container_id)
        
        logger.info(f"Periodic cleanup completed. Cleaned {len(expired_sessions)} sessions")
        
    except Exception as e:
        logger.error(f"Error in periodic cleanup: {e}", exc_info=True)
