"""
Local AI Platform - HTTP API Server
FastAPI-based backend API for the Local AI platform.
"""

import sys
from pathlib import Path
from typing import Dict, Any, Optional, List
import logging
from datetime import datetime

# Setup basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from fastapi import FastAPI, HTTPException, BackgroundTasks
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import JSONResponse
    from pydantic import BaseModel
    import uvicorn
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    logger.warning("FastAPI not available. Install with: pip install fastapi uvicorn")
    
    # Create dummy classes for type checking
    class BaseModel:
        pass
    
    class HTTPException(Exception):
        pass


if FASTAPI_AVAILABLE:
    # Pydantic models for API requests/responses
    class HealthResponse(BaseModel):
        """Health check response."""
        status: str
        version: str
        timestamp: str

    class AgentRequest(BaseModel):
        """Agent execution request."""
        message: str
        context: Optional[Dict[str, Any]] = None
        auto_approve: bool = False

    class AgentResponse(BaseModel):
        """Agent execution response."""
        success: bool
        response: str
        tasks_completed: int
        tasks_failed: int
        execution_time: float

    class ModelInfo(BaseModel):
        """Model information."""
        name: str
        version: str
        description: str
        parameters: str
        quantization: str
        context_length: int
        installed: bool

    class ChatRequest(BaseModel):
        """Chat request."""
        message: str
        model: Optional[str] = None
        session_id: Optional[str] = None
        temperature: float = 0.7
        max_tokens: int = 1024

    class ChatResponse(BaseModel):
        """Chat response."""
        response: str
        session_id: str
        model: str
        tokens_used: int

    class SessionInfo(BaseModel):
        """Session information."""
        session_id: str
        created_at: str
        last_activity: str
        message_count: int
        model: str

    class APIv1:
        """API v1 endpoints."""
        
        def __init__(self, app: FastAPI):
            """
            Initialize API v1.
            
            Args:
                app: FastAPI application instance
            """
            self.app = app
            self._setup_routes()
        
        def _setup_routes(self):
            """Setup API v1 routes."""
            self.app.get("/api/v1/health", response_model=HealthResponse)(self.health_check)
            self.app.post("/api/v1/agent", response_model=AgentResponse)(self.execute_agent)
            self.app.get("/api/v1/models", response_model=List[ModelInfo])(self.list_models)
            self.app.post("/api/v1/chat", response_model=ChatResponse)(self.chat)
            self.app.get("/api/v1/sessions", response_model=List[SessionInfo])(self.list_sessions)
            self.app.get("/api/v1/sessions/{session_id}", response_model=SessionInfo)(self.get_session)
            self.app.delete("/api/v1/sessions/{session_id}")(self.delete_session)
        
        async def health_check(self) -> HealthResponse:
            """Health check endpoint."""
            return HealthResponse(
                status="healthy",
                version="0.1.0",
                timestamp=datetime.utcnow().isoformat()
            )
        
        async def execute_agent(self, request: AgentRequest) -> AgentResponse:
            """Execute agent task."""
            import time
            start_time = time.time()
            
            try:
                # Import agent
                from agent.core import get_agent
                
                # Get agent
                agent = get_agent()
                
                # Set context if provided
                if request.context:
                    agent.set_context(request.context)
                
                # Set permission callback
                if not request.auto_approve:
                    def permission_callback(tool_name: str, parameters: dict) -> bool:
                        # For API, auto-deny dangerous operations without explicit approval
                        return False
                    agent.tool_executor.set_permission_callback(permission_callback)
                
                # Process message
                response = agent.process_message(request.message)
                
                execution_time = time.time() - start_time
                
                return AgentResponse(
                    success=True,
                    response=response,
                    tasks_completed=1,  # Simplified for now
                    tasks_failed=0,
                    execution_time=execution_time
                )
                
            except Exception as e:
                logger.error(f"Agent execution error: {e}")
                execution_time = time.time() - start_time
                return AgentResponse(
                    success=False,
                    response=f"Error: {str(e)}",
                    tasks_completed=0,
                    tasks_failed=1,
                    execution_time=execution_time
                )
        
        async def list_models(self) -> List[ModelInfo]:
            """List available models."""
            try:
                from models.manager import get_model_manager
                
                manager = get_model_manager()
                models = manager.list_models()
                
                model_infos = []
                for model in models:
                    model_infos.append(ModelInfo(
                        name=model.name,
                        version=str(model.version),
                        description=model.description,
                        parameters=str(model.parameters),
                        quantization=model.quantization,
                        context_length=model.context_length,
                        installed=model.installed
                    ))
                
                return model_infos
                
            except Exception as e:
                logger.error(f"Model list error: {e}")
                return []
        
        async def chat(self, request: ChatRequest) -> ChatResponse:
            """Execute chat request."""
            try:
                from backend.sessions import get_session_manager
                from backend.providers import get_provider_registry
                
                # Get session manager
                session_manager = get_session_manager()
                
                # Get or create session
                if request.session_id:
                    session = session_manager.get_session(request.session_id)
                    if not session:
                        raise HTTPException(status_code=404, detail="Session not found")
                else:
                    session = session_manager.create_session(model=request.model)
                
                # Get provider
                registry = get_provider_registry()
                provider = registry.get_default_provider()
                
                if not provider:
                    raise HTTPException(status_code=503, detail="No provider available")
                
                # Generate response
                response = await provider.generate(
                    messages=[{"role": "user", "content": request.message}],
                    temperature=request.temperature,
                    max_tokens=request.max_tokens
                )
                
                # Add messages to session
                session.add_message("user", request.message)
                session.add_message("assistant", response)
                
                return ChatResponse(
                    response=response,
                    session_id=session.session_id,
                    model=request.model or "default",
                    tokens_used=0  # Simplified for now
                )
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Chat error: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        async def list_sessions(self) -> List[SessionInfo]:
            """List all sessions."""
            try:
                from backend.sessions import get_session_manager
                
                session_manager = get_session_manager()
                sessions = session_manager.list_sessions()
                
                session_infos = []
                for session in sessions:
                    session_infos.append(SessionInfo(
                        session_id=session.session_id,
                        created_at=session.created_at.isoformat(),
                        last_activity=session.last_activity.isoformat(),
                        message_count=len(session.messages),
                        model=session.model
                    ))
                
                return session_infos
                
            except Exception as e:
                logger.error(f"Session list error: {e}")
                return []
        
        async def get_session(self, session_id: str) -> SessionInfo:
            """Get session information."""
            try:
                from backend.sessions import get_session_manager
                
                session_manager = get_session_manager()
                session = session_manager.get_session(session_id)
                
                if not session:
                    raise HTTPException(status_code=404, detail="Session not found")
                
                return SessionInfo(
                    session_id=session.session_id,
                    created_at=session.created_at.isoformat(),
                    last_activity=session.last_activity.isoformat(),
                    message_count=len(session.messages),
                    model=session.model
                )
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Session get error: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        async def delete_session(self, session_id: str):
            """Delete a session."""
            try:
                from backend.sessions import get_session_manager
                
                session_manager = get_session_manager()
                success = session_manager.delete_session(session_id)
                
                if not success:
                    raise HTTPException(status_code=404, detail="Session not found")
                
                return {"success": True}
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Session delete error: {e}")
                raise HTTPException(status_code=500, detail=str(e))


class Server:
    """Main API server."""
    
    def __init__(self, host: str = "127.0.0.1", port: int = 8000):
        """
        Initialize server.
        
        Args:
            host: Host to bind to
            port: Port to bind to
        """
        self.host = host
        self.port = port
        self.app = None
        self._setup_app()
    
    def _setup_app(self):
        """Setup FastAPI application."""
        if not FASTAPI_AVAILABLE:
            raise RuntimeError("FastAPI not available. Install with: pip install fastapi uvicorn")
        
        self.app = FastAPI(
            title="Local AI Platform API",
            description="API for the Local AI Development Platform",
            version="0.1.0"
        )
        
        # Add CORS middleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # Configure appropriately for production
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Setup API v1
        if FASTAPI_AVAILABLE:
            APIv1(self.app)
        
        logger.info("FastAPI application configured")
    
    def run(self):
        """Run the server."""
        if not self.app:
            raise RuntimeError("Application not configured")
        
        if not FASTAPI_AVAILABLE:
            raise RuntimeError("FastAPI not available. Install with: pip install fastapi uvicorn")
        
        logger.info(f"Starting server on {self.host}:{self.port}")
        uvicorn.run(self.app, host=self.host, port=self.port, log_level="info")


def create_server(host: str = "127.0.0.1", port: int = 8000) -> Server:
    """
    Create API server instance.
    
    Args:
        host: Host to bind to
        port: Port to bind to
        
    Returns:
        Server instance
    """
    return Server(host, port)


# Example usage and testing
if __name__ == "__main__":
    if not FASTAPI_AVAILABLE:
        print("FastAPI not available. Install with: pip install fastapi uvicorn")
        print("This is an optional dependency for the backend API server.")
        print("The CLI and agent functionality work without it.")
        sys.exit(0)
    
    # Create and run server
    server = create_server(host="127.0.0.1", port=8000)
    server.run()
