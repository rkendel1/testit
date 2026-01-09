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
        # Get DOCKER_HOST from environment, if set
        docker_host = os.environ.get('DOCKER_HOST')
        
        if docker_host and docker_host.startswith('unix://'):
            # Explicitly pass the base_url for unix sockets to avoid URL parsing issues
            # This handles cases where docker.from_env() might misparse the URL
            logger.info("Using explicit unix socket for Docker client initialization")
            return docker.DockerClient(base_url=docker_host)
        else:
            # Fall back to docker.from_env() which will use default socket
            # and handle all Docker environment variables automatically (including TLS)
            logger.info("Using docker.from_env() for Docker client initialization")
            return docker.from_env()
    except Exception as e:
        logger.error(f"Failed to initialize Docker client: {e}")
        raise
