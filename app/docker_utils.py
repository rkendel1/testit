"""
Shared Docker client utilities
"""
import os
import logging
import docker

logger = logging.getLogger(__name__)


def create_docker_client():
    """
    Create a Docker client with proper URL handling
    
    Returns:
        docker.DockerClient: Configured Docker client
        
    Raises:
        Exception: If Docker client initialization fails
    """
    try:
        # Use docker.from_env() which properly handles the DOCKER_HOST environment variable
        # and avoids the http+docker URL scheme issue present in docker-py 7.x versions
        # when using docker.DockerClient(base_url=...)
        return docker.from_env()
    except Exception as e:
        logger.error(f"Failed to initialize Docker client: {e}")
        raise
