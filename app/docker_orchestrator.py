import docker
import logging
import os
from typing import Optional, Tuple, Dict
from pathlib import Path
from app.config import get_settings
from app.models import LanguageType

logger = logging.getLogger(__name__)
settings = get_settings()


class DockerOrchestrator:
    """Handles Docker operations for building and running containers"""
    
    def __init__(self):
        """Initialize orchestrator with lazy Docker client initialization"""
        self._client = None
    
    @property
    def client(self):
        """Lazy initialization of Docker client"""
        if self._client is None:
            try:
                # Use DockerClient with explicit base_url to avoid http+docker scheme issues
                # docker.from_env() can fail with newer docker library versions
                docker_host = os.environ.get('DOCKER_HOST', 'unix:///var/run/docker.sock')
                
                # Ensure proper URL format
                if docker_host.startswith('unix://'):
                    base_url = docker_host
                elif docker_host.startswith('/'):
                    base_url = f'unix://{docker_host}'
                else:
                    base_url = docker_host
                
                self._client = docker.DockerClient(base_url=base_url)
            except Exception as e:
                logger.error(f"Failed to initialize Docker client: {e}")
                raise
        return self._client
    
    def build_image(self, repo_path: str, dockerfile_content: str, tag: str) -> Tuple[bool, str]:
        """
        Build a Docker image from the given Dockerfile
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            # Write Dockerfile
            dockerfile_path = Path(repo_path) / "Dockerfile"
            with open(dockerfile_path, 'w') as f:
                f.write(dockerfile_content)
            
            logger.info(f"Building image with tag: {tag}")
            
            # Build image
            image, build_logs = self.client.images.build(
                path=repo_path,
                tag=tag,
                rm=True,
                forcerm=True,
                timeout=settings.build_timeout_seconds
            )
            
            # Collect build logs
            logs = []
            for log in build_logs:
                if 'stream' in log:
                    logs.append(log['stream'])
                elif 'error' in log:
                    logs.append(f"ERROR: {log['error']}")
            
            log_output = ''.join(logs)
            logger.info(f"Image built successfully: {tag}")
            
            return True, log_output
            
        except docker.errors.BuildError as e:
            error_msg = f"Build failed: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
        except Exception as e:
            error_msg = f"Unexpected error during build: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def run_container(
        self, 
        image_tag: str, 
        container_name: str,
        language: LanguageType,
        ports: Optional[Dict[int, int]] = None
    ) -> Tuple[bool, Optional[str], str]:
        """
        Run a container from the built image
        
        Returns:
            Tuple of (success: bool, container_id: Optional[str], message: str)
        """
        try:
            # Default ports based on language
            if ports is None:
                ports = self._get_default_ports(language)
            
            logger.info(f"Running container: {container_name} from image: {image_tag}")
            
            container = self.client.containers.run(
                image_tag,
                name=container_name,
                detach=True,
                ports=ports,
                mem_limit=settings.container_memory_limit,
                cpu_period=100000,
                cpu_quota=int(settings.container_cpu_limit * 100000),
                remove=False,  # Don't auto-remove so we can manage lifecycle
                labels={
                    "managed_by": "testit",
                    "language": language.value
                }
            )
            
            logger.info(f"Container started: {container.id}")
            return True, container.id, "Container started successfully"
            
        except docker.errors.ImageNotFound:
            error_msg = f"Image not found: {image_tag}"
            logger.error(error_msg)
            return False, None, error_msg
        except docker.errors.APIError as e:
            error_msg = f"Docker API error: {str(e)}"
            logger.error(error_msg)
            return False, None, error_msg
        except Exception as e:
            error_msg = f"Unexpected error running container: {str(e)}"
            logger.error(error_msg)
            return False, None, error_msg
    
    def stop_container(self, container_id: str) -> Tuple[bool, str]:
        """
        Stop and remove a container
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            container = self.client.containers.get(container_id)
            container.stop(timeout=10)
            container.remove()
            logger.info(f"Container stopped and removed: {container_id}")
            return True, "Container stopped and removed"
        except docker.errors.NotFound:
            return False, f"Container not found: {container_id}"
        except Exception as e:
            error_msg = f"Error stopping container: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def get_container_status(self, container_id: str) -> Tuple[bool, Optional[str]]:
        """
        Get container status
        
        Returns:
            Tuple of (exists: bool, status: Optional[str])
        """
        try:
            container = self.client.containers.get(container_id)
            return True, container.status
        except docker.errors.NotFound:
            return False, None
        except Exception as e:
            logger.error(f"Error getting container status: {e}")
            return False, None
    
    def cleanup_old_containers(self) -> int:
        """
        Cleanup containers managed by testit
        
        NOTE: This method cleans up ALL containers with the testit label.
        For production, this should integrate with SessionManager to only
        cleanup truly expired sessions.
        
        Returns:
            Number of containers cleaned up
        """
        try:
            containers = self.client.containers.list(
                all=True,
                filters={"label": "managed_by=testit"}
            )
            
            count = 0
            for container in containers:
                try:
                    # TODO: Check session expiration before cleanup
                    container.stop(timeout=5)
                    container.remove()
                    count += 1
                    logger.info(f"Cleaned up container: {container.id}")
                except Exception as e:
                    logger.warning(f"Failed to cleanup container {container.id}: {e}")
            
            return count
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
            return 0
    
    def _get_default_ports(self, language: LanguageType) -> Dict[int, int]:
        """Get default port mappings based on language"""
        port_mappings = {
            LanguageType.PYTHON: {'8000/tcp': 8000, '8888/tcp': 8888},
            LanguageType.NODE: {'3000/tcp': 3000, '8080/tcp': 8080},
            LanguageType.JAVA: {'8080/tcp': 8080},
            LanguageType.GO: {'8080/tcp': 8080},
        }
        return port_mappings.get(language, {'8080/tcp': 8080})
