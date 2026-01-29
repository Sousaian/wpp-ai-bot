import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional
from loguru import logger


class SessionManager:
    """Manage user sessions and conversation threads"""
    
    def __init__(self, storage_path: str = "data/sessions.json"):
        self.storage_path = Path(storage_path)
        self.sessions: Dict[str, dict] = {}
        self._load_sessions()
    
    def _load_sessions(self):
        """Load sessions from file"""
        if self.storage_path.exists():
            try:
                with open(self.storage_path, "r") as f:
                    self.sessions = json.load(f)
                logger.info(f"📂 Loaded {len(self.sessions)} sessions from storage")
            except Exception as e:
                logger.error(f"❌ Error loading sessions: {e}")
                self.sessions = {}
        else:
            logger.info("📂 No existing sessions found, starting fresh")
            self.sessions = {}
    
    def _save_sessions(self):
        """Save sessions to file"""
        try:
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.storage_path, "w") as f:
                json.dump(self.sessions, f, indent=2)
            logger.debug("💾 Sessions saved to storage")
        except Exception as e:
            logger.error(f"❌ Error saving sessions: {e}")
    
    def get_session(self, phone: str) -> Optional[dict]:
        """Get session for a phone number"""
        return self.sessions.get(phone)
    
    def create_session(self, phone: str, conversation_id: str) -> dict:
        """Create new session for a phone number"""
        session = {
            "conversation_id": conversation_id,
            "handler": "bot",  # or "human"
            "created_at": datetime.now().isoformat(),
            "last_interaction": datetime.now().isoformat(),
            "message_count": 0
        }
        self.sessions[phone] = session
        self._save_sessions()
        logger.info(f"✨ New session created for {phone[:8]}...")
        return session
    
    def update_session(self, phone: str, **kwargs):
        """Update session data"""
        if phone in self.sessions:
            self.sessions[phone].update(kwargs)
            self.sessions[phone]["last_interaction"] = datetime.now().isoformat()
            self._save_sessions()
            logger.debug(f"🔄 Session updated for {phone[:8]}...")
    
    def increment_message_count(self, phone: str):
        """Increment message count for session"""
        if phone in self.sessions:
            self.sessions[phone]["message_count"] = self.sessions[phone].get("message_count", 0) + 1
            self._save_sessions()
    
    def set_handler(self, phone: str, handler: str):
        """Set handler type (bot or human)"""
        if phone in self.sessions:
            self.sessions[phone]["handler"] = handler
            self._save_sessions()
            logger.info(f"👤 Handler changed to '{handler}' for {phone[:8]}...")
    
    def is_bot_handler(self, phone: str) -> bool:
        """Check if session is handled by bot"""
        session = self.get_session(phone)
        return session and session.get("handler") == "bot"
    
    def delete_session(self, phone: str):
        """Delete session for a phone number"""
        if phone in self.sessions:
            del self.sessions[phone]
            self._save_sessions()
            logger.info(f"🗑️ Session deleted for {phone[:8]}...")
    
    def get_all_sessions(self) -> Dict[str, dict]:
        """Get all sessions"""
        return self.sessions
    
    def get_active_sessions_count(self) -> int:
        """Get count of active sessions"""
        return len(self.sessions)


# Singleton instance
session_manager = SessionManager()