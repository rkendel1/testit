import redis
import json
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from app.config import get_settings
from app.models import SessionStatus, LanguageType

logger = logging.getLogger(__name__)
settings = get_settings()


class SessionManager:
    """Manages ephemeral container sessions"""
    
    SESSION_KEY_PREFIX = "session:"
    SESSION_INDEX_KEY = "sessions:active"
    
    def __init__(self):
        """Initialize Redis connection"""
        try:
            self.redis_client = redis.from_url(settings.redis_url)
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
    
    def create_session(
        self, 
        session_id: str, 
        container_id: str, 
        language: LanguageType,
        task_id: str
    ) -> Dict:
        """Create a new session"""
        now = datetime.utcnow()
        expires_at = now + timedelta(minutes=settings.session_timeout_minutes)
        
        session_data = {
            "session_id": session_id,
            "container_id": container_id,
            "language": language.value,
            "status": SessionStatus.RUNNING.value,
            "task_id": task_id,
            "created_at": now.isoformat(),
            "expires_at": expires_at.isoformat(),
            "last_accessed": now.isoformat()
        }
        
        # Store session data
        key = f"{self.SESSION_KEY_PREFIX}{session_id}"
        self.redis_client.setex(
            key,
            settings.session_timeout_minutes * 60,
            json.dumps(session_data)
        )
        
        # Add to active sessions index
        self.redis_client.sadd(self.SESSION_INDEX_KEY, session_id)
        
        logger.info(f"Session created: {session_id}")
        return session_data
    
    def get_session(self, session_id: str) -> Optional[Dict]:
        """Get session data"""
        key = f"{self.SESSION_KEY_PREFIX}{session_id}"
        data = self.redis_client.get(key)
        
        if data:
            session = json.loads(data)
            # Update last accessed time
            session["last_accessed"] = datetime.utcnow().isoformat()
            self.redis_client.setex(
                key,
                settings.session_timeout_minutes * 60,
                json.dumps(session)
            )
            return session
        
        return None
    
    def update_session_status(self, session_id: str, status: SessionStatus) -> bool:
        """Update session status"""
        session = self.get_session(session_id)
        if not session:
            return False
        
        session["status"] = status.value
        key = f"{self.SESSION_KEY_PREFIX}{session_id}"
        
        if status == SessionStatus.STOPPED:
            # Remove from Redis when stopped
            self.redis_client.delete(key)
            self.redis_client.srem(self.SESSION_INDEX_KEY, session_id)
        else:
            self.redis_client.setex(
                key,
                settings.session_timeout_minutes * 60,
                json.dumps(session)
            )
        
        logger.info(f"Session {session_id} status updated to {status.value}")
        return True
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a session"""
        key = f"{self.SESSION_KEY_PREFIX}{session_id}"
        result = self.redis_client.delete(key)
        self.redis_client.srem(self.SESSION_INDEX_KEY, session_id)
        
        if result:
            logger.info(f"Session deleted: {session_id}")
        return bool(result)
    
    def get_all_active_sessions(self) -> List[Dict]:
        """Get all active sessions"""
        session_ids = self.redis_client.smembers(self.SESSION_INDEX_KEY)
        sessions = []
        
        for session_id in session_ids:
            session_id_str = session_id.decode('utf-8') if isinstance(session_id, bytes) else session_id
            session = self.get_session(session_id_str)
            if session:
                sessions.append(session)
        
        return sessions
    
    def cleanup_expired_sessions(self) -> List[str]:
        """
        Find sessions that should be cleaned up
        Returns list of expired session IDs
        """
        expired_sessions = []
        sessions = self.get_all_active_sessions()
        now = datetime.utcnow()
        
        for session in sessions:
            try:
                expires_at = datetime.fromisoformat(session["expires_at"])
                if now > expires_at:
                    expired_sessions.append(session["session_id"])
            except Exception as e:
                logger.warning(f"Error checking expiration for session {session.get('session_id')}: {e}")
        
        logger.info(f"Found {len(expired_sessions)} expired sessions")
        return expired_sessions
