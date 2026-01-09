from pydantic import BaseModel, HttpUrl
from typing import Optional, Dict, List
from enum import Enum


class LanguageType(str, Enum):
    """Supported languages"""
    PYTHON = "python"
    NODE = "node"
    JAVA = "java"
    GO = "go"
    UNKNOWN = "unknown"


class BuildStatus(str, Enum):
    """Build status"""
    PENDING = "pending"
    BUILDING = "building"
    SUCCESS = "success"
    FAILED = "failed"


class SessionStatus(str, Enum):
    """Session status"""
    STARTING = "starting"
    RUNNING = "running"
    STOPPED = "stopped"
    FAILED = "failed"


class SubmitRepoRequest(BaseModel):
    """Request to submit a GitHub repository"""
    repo_url: HttpUrl


class SubmitRepoResponse(BaseModel):
    """Response after submitting a repository"""
    task_id: str
    status: BuildStatus
    message: str


class BuildStatusResponse(BaseModel):
    """Build status response"""
    task_id: str
    status: BuildStatus
    language: Optional[LanguageType] = None
    dependencies: Optional[Dict[str, List[str]]] = None
    logs: Optional[str] = None
    session_id: Optional[str] = None
    container_id: Optional[str] = None
    access_url: Optional[str] = None


class SessionInfo(BaseModel):
    """Session information"""
    session_id: str
    container_id: str
    status: SessionStatus
    language: LanguageType
    created_at: str
    expires_at: str
    access_url: Optional[str] = None
