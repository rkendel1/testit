from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings"""
    
    # Redis
    redis_url: str = "redis://localhost:6379/0"
    
    # Celery
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/0"
    
    # Docker
    docker_socket: str = "unix://var/run/docker.sock"
    
    # Session settings
    session_timeout_minutes: int = 60  # 30-60 minutes per session
    session_cleanup_interval_minutes: int = 5
    
    # Container settings
    container_memory_limit: str = "2g"  # 1-2 GB RAM
    container_cpu_limit: float = 2.0  # 1-2 CPU cores
    container_cpu_count: int = 2
    
    # Build settings
    build_timeout_seconds: int = 300
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
