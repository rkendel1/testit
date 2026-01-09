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
        
        return docker.DockerClient(base_url=base_url)
    except Exception as e:
        logger.error(f"Failed to initialize Docker client: {e}")
        raise
