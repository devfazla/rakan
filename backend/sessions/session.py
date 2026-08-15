"""
Local AI Platform - Session Management
Manages conversation sessions and message history.
"""

import sys
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime
import json
import uuid
import logging

# Setup basic logging without agent.core dependency
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class Message:
    """Single message in a conversation."""
    role: str  # 'user', 'assistant', 'system'
    content: str
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    tokens: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Session:
    """Conversation session."""
    session_id: str
    model: str
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    messages: List[Message] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_message(self, role: str, content: str, tokens: int = 0, metadata: Optional[Dict[str, Any]] = None):
        """Add a message to the session."""
        message = Message(
            role=role,
            content=content,
            tokens=tokens,
            metadata=metadata or {}
        )
        self.messages.append(message)
        self.updated_at = datetime.utcnow().isoformat()
    
    def get_conversation_history(self, max_messages: Optional[int] = None) -> List[Message]:
        """Get conversation history, optionally limited."""
        if max_messages:
            return self.messages[-max_messages:]
        return self.messages
    
    def clear(self):
        """Clear all messages from the session."""
        self.messages = []
        self.updated_at = datetime.utcnow().isoformat()
    
    def get_total_tokens(self) -> int:
        """Get total tokens used in the session."""
        return sum(msg.tokens for msg in self.messages)


class SessionManager:
    """Manages conversation sessions."""
    
    def __init__(self, storage_path: Optional[str] = None):
        """
        Initialize session manager.
        
        Args:
            storage_path: Path to store session data
        """
        self.logger = logger
        self.storage_path = Path(storage_path) if storage_path else Path.home() / '.local-ai' / 'sessions'
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self.sessions: Dict[str, Session] = {}
        self._load_sessions()
    
    def _load_sessions(self):
        """Load sessions from storage."""
        self.logger.info("Loading sessions from storage...")
        
        # Load session index
        index_file = self.storage_path / 'index.json'
        if index_file.exists():
            try:
                with open(index_file, 'r') as f:
                    index = json.load(f)
                
                for session_id, session_data in index.items():
                    session = Session(
                        session_id=session_id,
                        model=session_data.get('model', 'unknown'),
                        created_at=session_data.get('created_at'),
                        updated_at=session_data.get('updated_at'),
                        metadata=session_data.get('metadata', {})
                    )
                    
                    # Load messages
                    messages_file = self.storage_path / f'{session_id}_messages.json'
                    if messages_file.exists():
                        with open(messages_file, 'r') as f:
                            messages_data = json.load(f)
                            for msg_data in messages_data:
                                session.messages.append(Message(**msg_data))
                    
                    self.sessions[session_id] = session
                
                self.logger.info(f"Loaded {len(self.sessions)} sessions")
                
            except Exception as e:
                self.logger.error(f"Failed to load sessions: {e}")
    
    def _save_session(self, session: Session):
        """Save a single session to storage."""
        try:
            # Save session metadata
            session_file = self.storage_path / f'{session.session_id}.json'
            session_data = {
                'session_id': session.session_id,
                'model': session.model,
                'created_at': session.created_at,
                'updated_at': session.updated_at,
                'metadata': dict(session.metadata)  # Convert to dict if needed
            }
            
            with open(session_file, 'w') as f:
                json.dump(session_data, f, indent=2)
            
            # Save messages
            messages_file = self.storage_path / f'{session.session_id}_messages.json'
            messages_data = [
                {
                    'role': msg.role,
                    'content': msg.content,
                    'timestamp': msg.timestamp,
                    'tokens': msg.tokens,
                    'metadata': dict(msg.metadata)  # Convert to dict if needed
                }
                for msg in session.messages
            ]
            
            with open(messages_file, 'w') as f:
                json.dump(messages_data, f, indent=2)
            
        except Exception as e:
            self.logger.error(f"Failed to save session {session.session_id}: {e}")
    
    def _save_index(self):
        """Save session index."""
        try:
            index_file = self.storage_path / 'index.json'
            index = {}
            
            for session_id, session in self.sessions.items():
                index[session_id] = {
                    'model': session.model,
                    'created_at': session.created_at,
                    'updated_at': session.updated_at,
                    'metadata': session.metadata
                }
            
            with open(index_file, 'w') as f:
                json.dump(index, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Failed to save session index: {e}")
    
    def create_session(self, model: str, metadata: Optional[Dict[str, Any]] = None) -> Session:
        """
        Create a new session.
        
        Args:
            model: Model to use for the session
            metadata: Optional session metadata
            
        Returns:
            Created Session
        """
        session_id = str(uuid.uuid4())
        
        session = Session(
            session_id=session_id,
            model=model,
            metadata=metadata or {}
        )
        
        self.sessions[session_id] = session
        self._save_session(session)
        self._save_index()
        
        self.logger.info(f"Created session: {session_id}")
        return session
    
    def get_session(self, session_id: str) -> Optional[Session]:
        """
        Get a session by ID.
        
        Args:
            session_id: Session ID
            
        Returns:
            Session or None if not found
        """
        return self.sessions.get(session_id)
    
    def list_sessions(self) -> List[Dict[str, Any]]:
        """
        List all sessions.
        
        Returns:
            List of session information
        """
        sessions_info = []
        
        for session_id, session in self.sessions.items():
            sessions_info.append({
                'session_id': session_id,
                'model': session.model,
                'created_at': session.created_at,
                'updated_at': session.updated_at,
                'message_count': len(session.messages),
                'total_tokens': session.get_total_tokens()
            })
        
        return sorted(sessions_info, key=lambda x: x['updated_at'], reverse=True)
    
    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session.
        
        Args:
            session_id: Session ID
            
        Returns:
            True if successful, False otherwise
        """
        if session_id not in self.sessions:
            return False
        
        # Remove from memory
        del self.sessions[session_id]
        
        # Remove from storage
        try:
            session_file = self.storage_path / f'{session_id}.json'
            messages_file = self.storage_path / f'{session_id}_messages.json'
            
            if session_file.exists():
                session_file.unlink()
            if messages_file.exists():
                messages_file.unlink()
            
            self._save_index()
            self.logger.info(f"Deleted session: {session_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to delete session {session_id}: {e}")
            return False
    
    def clear_session(self, session_id: str) -> bool:
        """
        Clear messages from a session.
        
        Args:
            session_id: Session ID
            
        Returns:
            True if successful, False otherwise
        """
        session = self.get_session(session_id)
        if not session:
            return False
        
        session.clear()
        self._save_session(session)
        self._save_index()
        
        return True
    
    def add_message(self, session_id: str, role: str, content: str, tokens: int = 0, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Add a message to a session.
        
        Args:
            session_id: Session ID
            role: Message role
            content: Message content
            tokens: Token count
            metadata: Optional metadata
            
        Returns:
            True if successful, False otherwise
        """
        session = self.get_session(session_id)
        if not session:
            return False
        
        session.add_message(role, content, tokens, metadata)
        self._save_session(session)
        self._save_index()
        
        return True
    
    def get_conversation_context(self, session_id: str, max_messages: Optional[int] = None) -> str:
        """
        Get formatted conversation context for a session.
        
        Args:
            session_id: Session ID
            max_messages: Maximum number of messages to include
            
        Returns:
            Formatted conversation string
        """
        session = self.get_session(session_id)
        if not session:
            return ""
        
        messages = session.get_conversation_history(max_messages)
        
        context_lines = []
        for msg in messages:
            context_lines.append(f"{msg.role}: {msg.content}")
        
        return "\n".join(context_lines)


# Global session manager instance
_session_manager = None


def get_session_manager(storage_path: Optional[str] = None) -> SessionManager:
    """
    Get global session manager instance.
    
    Args:
        storage_path: Optional storage path
        
    Returns:
        SessionManager instance
    """
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager(storage_path)
    return _session_manager


# Example usage and testing
if __name__ == "__main__":
    # Test session management
    print("Testing Session Management...")
    
    manager = get_session_manager()
    
    # Create a session
    session = manager.create_session("qwen2.5-coder-1.5b-instruct", {"project": "test"})
    print(f"\nCreated session: {session.session_id}")
    
    # Add messages
    manager.add_message(session.session_id, "user", "Hello, how are you?")
    manager.add_message(session.session_id, "assistant", "I'm doing well, thank you!", tokens=10)
    manager.add_message(session.session_id, "user", "Can you help me with coding?")
    
    # Get conversation context
    context = manager.get_conversation_context(session.session_id)
    print(f"\nConversation context:\n{context}")
    
    # List sessions
    sessions = manager.list_sessions()
    print(f"\nSessions: {len(sessions)}")
    for session_info in sessions:
        print(f"  - {session_info['session_id']}: {session_info['message_count']} messages")
    
    # Clear session
    manager.clear_session(session.session_id)
    print(f"\nCleared session: {session.session_id}")
    
    # Delete session
    manager.delete_session(session.session_id)
    print(f"Deleted session: {session.session_id}")
    
    print("\nSession management test completed!")
