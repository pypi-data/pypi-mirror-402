"""
Supero AI Manager
Location: ~/supero/platform/infra/libs/py/src/supero/ai_manager.py

Provides fluent AI capabilities for tenant applications:
- Natural language chat with schema-aware tools
- Conversation session management
- Direct tool invocation
- Vector search for RAG

Architecture:
    Tenant App → Supero SDK → Platform Core → AI Service
    
    The same JWT token used for CRUD operations is forwarded
    to AI Service, which uses it for tool execution via Platform Core.

Example:
    >>> org = Supero.quickstart("acme-corp", jwt_token="...")
    >>> 
    >>> # Chat with AI
    >>> response = org.ai.chat("Show me all active projects")
    >>> print(response.content)
    >>> 
    >>> # Streaming chat
    >>> for chunk in org.ai.chat_stream("Summarize my tasks"):
    ...     print(chunk, end="", flush=True)
    >>> 
    >>> # Session management
    >>> session = org.ai.sessions.create()
    >>> org.ai.chat("What projects do I have?", session_id=session.id)
    >>> org.ai.chat("Add a new task to the first one", session_id=session.id)
    >>> 
    >>> # Direct tool invocation
    >>> tools = org.ai.tools.list()
    >>> result = org.ai.tools.invoke("list_projects", status="active")
"""

import json
import logging
from typing import Any, Dict, List, Optional, Iterator, Union, TYPE_CHECKING
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

if TYPE_CHECKING:
    from .platform_client import PlatformClient


# ============================================================================
# Data Models
# ============================================================================

class MessageRole(str, Enum):
    """Message roles in a conversation."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"


@dataclass
class Message:
    """A message in a conversation."""
    role: MessageRole
    content: str
    tool_calls: Optional[List[Dict[str, Any]]] = None
    tool_call_id: Optional[str] = None
    name: Optional[str] = None
    timestamp: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to API format."""
        data = {
            "role": self.role.value if isinstance(self.role, MessageRole) else self.role,
            "content": self.content
        }
        if self.tool_calls:
            data["tool_calls"] = self.tool_calls
        if self.tool_call_id:
            data["tool_call_id"] = self.tool_call_id
        if self.name:
            data["name"] = self.name
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
        """Create from API response."""
        return cls(
            role=MessageRole(data.get("role", "assistant")),
            content=data.get("content", ""),
            tool_calls=data.get("tool_calls"),
            tool_call_id=data.get("tool_call_id"),
            name=data.get("name"),
            timestamp=datetime.fromisoformat(data["timestamp"]) if data.get("timestamp") else None
        )


@dataclass
class ChatResponse:
    """Response from AI chat."""
    content: str
    role: MessageRole = MessageRole.ASSISTANT
    tool_calls: Optional[List[Dict[str, Any]]] = None
    tool_results: Optional[List[Dict[str, Any]]] = None
    session_id: Optional[str] = None
    usage: Optional[Dict[str, int]] = None
    model: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ChatResponse':
        """Create from API response."""
        return cls(
            content=data.get("content", ""),
            role=MessageRole(data.get("role", "assistant")),
            tool_calls=data.get("tool_calls"),
            tool_results=data.get("tool_results"),
            session_id=data.get("session_id"),
            usage=data.get("usage"),
            model=data.get("model")
        )


@dataclass
class Session:
    """A conversation session."""
    id: str
    domain_name: str
    created_at: datetime
    updated_at: datetime
    message_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Session':
        """Create from API response."""
        return cls(
            id=data["session_id"],
            domain_name=data.get("domain_name", ""),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.now(),
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else datetime.now(),
            message_count=data.get("message_count", 0),
            metadata=data.get("metadata", {})
        )


@dataclass
class Tool:
    """An AI tool definition."""
    name: str
    description: str
    parameters: Dict[str, Any]
    schema_name: Optional[str] = None
    operation: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Tool':
        """Create from API response."""
        return cls(
            name=data["name"],
            description=data.get("description", ""),
            parameters=data.get("parameters", {}),
            schema_name=data.get("schema_name"),
            operation=data.get("operation")
        )


@dataclass
class ToolResult:
    """Result from tool invocation."""
    tool_name: str
    success: bool
    result: Any
    error: Optional[str] = None
    execution_time_ms: Optional[float] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ToolResult':
        """Create from API response."""
        return cls(
            tool_name=data.get("tool_name", ""),
            success=data.get("success", True),
            result=data.get("result"),
            error=data.get("error"),
            execution_time_ms=data.get("execution_time_ms")
        )


@dataclass
class VectorSearchResult:
    """Result from vector similarity search."""
    id: str
    content: str
    score: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'VectorSearchResult':
        """Create from API response."""
        return cls(
            id=data["id"],
            content=data.get("content", ""),
            score=data.get("score", 0.0),
            metadata=data.get("metadata", {})
        )


# ============================================================================
# Session Manager
# ============================================================================

class SessionManager:
    """
    Manage conversation sessions.
    
    Sessions maintain conversation history across multiple chat interactions,
    enabling context-aware conversations.
    
    Example:
        >>> sessions = org.ai.sessions
        >>> 
        >>> # Create new session
        >>> session = sessions.create(metadata={"purpose": "project-planning"})
        >>> 
        >>> # Use session in chat
        >>> org.ai.chat("What projects exist?", session_id=session.id)
        >>> org.ai.chat("Create a new one called Backend", session_id=session.id)
        >>> 
        >>> # List sessions
        >>> all_sessions = sessions.list()
        >>> 
        >>> # Get session history
        >>> history = sessions.get_history(session.id)
        >>> 
        >>> # Delete session
        >>> sessions.delete(session.id)
    """
    
    def __init__(self, ai_manager: 'AIManager'):
        self._ai_manager = ai_manager
        self._logger = ai_manager._logger
    
    def create(self, metadata: Optional[Dict[str, Any]] = None) -> Session:
        """
        Create a new conversation session.
        
        Args:
            metadata: Optional metadata to attach to session
            
        Returns:
            Session object with ID for subsequent chats
        """
        response = self._ai_manager._request(
            "POST",
            "/ai/v1/sessions",
            json={"metadata": metadata or {}}
        )
        return Session.from_dict(response)
    
    def list(self, limit: int = 20, offset: int = 0) -> List[Session]:
        """
        List conversation sessions.
        
        Args:
            limit: Maximum sessions to return
            offset: Pagination offset
            
        Returns:
            List of Session objects
        """
        response = self._ai_manager._request(
            "GET",
            "/ai/v1/sessions",
            params={"limit": limit, "offset": offset}
        )
        sessions = response.get("sessions", [])
        return [Session.from_dict(s) for s in sessions]
    
    def get(self, session_id: str) -> Session:
        """
        Get session details.
        
        Args:
            session_id: Session ID
            
        Returns:
            Session object
        """
        response = self._ai_manager._request(
            "GET",
            f"/ai/v1/sessions/{session_id}"
        )
        return Session.from_dict(response)
    
    def get_history(self, session_id: str) -> List[Message]:
        """
        Get conversation history for a session.
        
        Args:
            session_id: Session ID
            
        Returns:
            List of Message objects
        """
        response = self._ai_manager._request(
            "GET",
            f"/ai/v1/sessions/{session_id}"
        )
        messages = response.get("messages", [])
        return [Message.from_dict(m) for m in messages]
    
    def delete(self, session_id: str) -> bool:
        """
        Delete a session and its history.
        
        Args:
            session_id: Session ID
            
        Returns:
            True if deleted successfully
        """
        self._ai_manager._request(
            "DELETE",
            f"/ai/v1/sessions/{session_id}"
        )
        return True
    
    def clear_history(self, session_id: str) -> bool:
        """
        Clear session history while keeping the session.
        
        Args:
            session_id: Session ID
            
        Returns:
            True if cleared successfully
        """
        self._ai_manager._request(
            "POST",
            f"/ai/v1/sessions/{session_id}/clear"
        )
        return True


# ============================================================================
# Tool Manager
# ============================================================================

class ToolManager:
    """
    Manage AI tools (auto-generated from schemas).
    
    Tools are automatically generated from your domain's schemas.
    Each schema gets CRUD tools (create, read, update, delete, list).
    
    Example:
        >>> tools = org.ai.tools
        >>> 
        >>> # List available tools
        >>> all_tools = tools.list()
        >>> for tool in all_tools:
        ...     print(f"{tool.name}: {tool.description}")
        >>> 
        >>> # Invoke tool directly
        >>> result = tools.invoke("list_projects", status="active")
        >>> print(result.result)
        >>> 
        >>> # Refresh tools (after schema changes)
        >>> tools.refresh()
    """
    
    def __init__(self, ai_manager: 'AIManager'):
        self._ai_manager = ai_manager
        self._logger = ai_manager._logger
        self._cache: Optional[List[Tool]] = None
    
    def list(self, refresh: bool = False) -> List[Tool]:
        """
        List available tools.
        
        Tools are generated from domain schemas and include:
        - create_<schema>: Create new objects
        - get_<schema>: Get object by ID
        - list_<schema>: List objects with filters
        - update_<schema>: Update object
        - delete_<schema>: Delete object
        
        Args:
            refresh: Force refresh from server
            
        Returns:
            List of Tool objects
        """
        if self._cache is not None and not refresh:
            return self._cache
        
        response = self._ai_manager._request(
            "GET",
            "/ai/v1/tools"
        )
        tools = response.get("tools", [])
        self._cache = [Tool.from_dict(t) for t in tools]
        return self._cache
    
    def get(self, tool_name: str) -> Optional[Tool]:
        """
        Get tool by name.
        
        Args:
            tool_name: Tool name (e.g., "list_projects")
            
        Returns:
            Tool object or None if not found
        """
        tools = self.list()
        for tool in tools:
            if tool.name == tool_name:
                return tool
        return None
    
    def invoke(self, tool_name: str, **kwargs) -> ToolResult:
        """
        Invoke a tool directly (without LLM).
        
        Useful for programmatic tool access when you know exactly
        what operation you want.
        
        Args:
            tool_name: Name of tool to invoke
            **kwargs: Tool parameters
            
        Returns:
            ToolResult with operation result
            
        Example:
            >>> result = tools.invoke("list_projects", status="active", limit=10)
            >>> projects = result.result
        """
        response = self._ai_manager._request(
            "POST",
            f"/ai/v1/tools/{tool_name}/invoke",
            json={"parameters": kwargs}
        )
        return ToolResult.from_dict(response)
    
    def refresh(self) -> List[Tool]:
        """
        Refresh tools cache from server.
        
        Call after uploading new schemas to get updated tools.
        
        Returns:
            Updated list of tools
        """
        self._ai_manager._request(
            "POST",
            "/ai/v1/tools/refresh"
        )
        self._cache = None
        return self.list(refresh=True)
    
    def for_schema(self, schema_name: str) -> List[Tool]:
        """
        Get tools for a specific schema.
        
        Args:
            schema_name: Schema name (e.g., "Project")
            
        Returns:
            List of tools for that schema
        """
        all_tools = self.list()
        schema_lower = schema_name.lower()
        return [
            t for t in all_tools 
            if t.schema_name and t.schema_name.lower() == schema_lower
        ]


# ============================================================================
# Vector Manager
# ============================================================================

class VectorManager:
    """
    Manage vector embeddings for semantic search (RAG).
    
    Index documents and search by semantic similarity for
    retrieval-augmented generation.
    
    Example:
        >>> vectors = org.ai.vectors
        >>> 
        >>> # Index a document
        >>> vectors.index(
        ...     content="Project Alpha is our main backend initiative...",
        ...     metadata={"type": "project_doc", "project_id": "uuid-123"}
        ... )
        >>> 
        >>> # Search by similarity
        >>> results = vectors.search("backend projects", limit=5)
        >>> for r in results:
        ...     print(f"[{r.score:.2f}] {r.content[:100]}...")
    """
    
    def __init__(self, ai_manager: 'AIManager'):
        self._ai_manager = ai_manager
        self._logger = ai_manager._logger
    
    def index(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        document_id: Optional[str] = None
    ) -> str:
        """
        Index content for vector search.
        
        Args:
            content: Text content to index
            metadata: Optional metadata for filtering
            document_id: Optional ID (auto-generated if not provided)
            
        Returns:
            Document ID
        """
        response = self._ai_manager._request(
            "POST",
            "/ai/v1/vectors/index",
            json={
                "content": content,
                "metadata": metadata or {},
                "document_id": document_id
            }
        )
        return response.get("document_id", "")
    
    def search(
        self,
        query: str,
        limit: int = 10,
        min_score: float = 0.0,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[VectorSearchResult]:
        """
        Search indexed content by semantic similarity.
        
        Args:
            query: Search query text
            limit: Maximum results
            min_score: Minimum similarity score (0-1)
            filters: Metadata filters
            
        Returns:
            List of search results ordered by relevance
        """
        response = self._ai_manager._request(
            "POST",
            "/ai/v1/vectors/search",
            json={
                "query": query,
                "limit": limit,
                "min_score": min_score,
                "filters": filters or {}
            }
        )
        results = response.get("results", [])
        return [VectorSearchResult.from_dict(r) for r in results]
    
    def delete(self, document_id: str) -> bool:
        """
        Delete indexed document.
        
        Args:
            document_id: Document ID to delete
            
        Returns:
            True if deleted
        """
        self._ai_manager._request(
            "DELETE",
            f"/ai/v1/vectors/{document_id}"
        )
        return True
    
    def bulk_index(
        self,
        documents: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Index multiple documents.
        
        Args:
            documents: List of {"content": str, "metadata": dict, "document_id": str}
            
        Returns:
            Summary of indexed documents
        """
        response = self._ai_manager._request(
            "POST",
            "/ai/v1/vectors/bulk-index",
            json={"documents": documents}
        )
        return response


# ============================================================================
# Main AI Manager
# ============================================================================

class AIManager:
    """
    AI capabilities for Supero domains.
    
    Provides natural language interaction with your domain data through
    schema-aware AI tools.
    
    Access via org.ai property:
    
        >>> org = Supero.quickstart("acme-corp", jwt_token="...")
        >>> 
        >>> # Simple chat
        >>> response = org.ai.chat("What projects do we have?")
        >>> print(response.content)
        >>> 
        >>> # Chat with session (maintains context)
        >>> session = org.ai.sessions.create()
        >>> org.ai.chat("Show active projects", session_id=session.id)
        >>> org.ai.chat("Create a task for the first one", session_id=session.id)
        >>> 
        >>> # Streaming response
        >>> for chunk in org.ai.chat_stream("Explain our project structure"):
        ...     print(chunk, end="", flush=True)
        >>> 
        >>> # Direct tool access
        >>> tools = org.ai.tools.list()
        >>> result = org.ai.tools.invoke("list_projects", status="active")
        >>> 
        >>> # Vector search for RAG
        >>> org.ai.vectors.index(content="...", metadata={...})
        >>> results = org.ai.vectors.search("backend architecture")
    
    The AI uses the same JWT token as CRUD operations, ensuring proper
    authorization for all data access.
    """
    
    def __init__(
        self,
        platform_client: 'PlatformClient',
        logger: logging.Logger = None
    ):
        """
        Initialize AI Manager.
        
        Args:
            domain_name: Domain name for context
            platform_client: Platform client for API calls (connects to api.supero.dev)
            logger: Optional logger
            
        Architecture:
            SDK → api.supero.dev/ai/v1/* (Platform Core)
                        │
                        ▼ (validates JWT, proxies)
                  ai-service:8090/ai/v1/* (internal)
            
        Example:
            ai_mgr = AIManager(domain_name, platform_client)
            response = ai_mgr.chat("Show me active projects")
        """
        self._platform_client = platform_client
        self._domain_name = platform_client.domain_name
        self._logger = logger or logging.getLogger(f"supero.ai.{self._domain_name}")
        
        # Lazy-loaded sub-managers
        self._sessions: Optional[SessionManager] = None
        self._tools: Optional[ToolManager] = None
        self._vectors: Optional[VectorManager] = None
        
        # Default settings
        self._default_model: Optional[str] = None
        self._default_max_tokens: int = 4000
        self._default_temperature: float = 0.7
    
    # ========================================================================
    # Properties for sub-managers
    # ========================================================================
    
    @property
    def sessions(self) -> SessionManager:
        """
        Session management for multi-turn conversations.
        
        Example:
            >>> session = org.ai.sessions.create()
            >>> org.ai.chat("Hello", session_id=session.id)
        """
        if self._sessions is None:
            self._sessions = SessionManager(self)
        return self._sessions
    
    @property
    def tools(self) -> ToolManager:
        """
        Tool management for schema-generated operations.
        
        Example:
            >>> tools = org.ai.tools.list()
            >>> result = org.ai.tools.invoke("list_projects")
        """
        if self._tools is None:
            self._tools = ToolManager(self)
        return self._tools
    
    @property
    def vectors(self) -> VectorManager:
        """
        Vector store for semantic search and RAG.
        
        Example:
            >>> org.ai.vectors.index(content="...", metadata={})
            >>> results = org.ai.vectors.search("query")
        """
        if self._vectors is None:
            self._vectors = VectorManager(self)
        return self._vectors
    
    # ========================================================================
    # Configuration
    # ========================================================================
    
    def configure(
        self,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None
    ) -> 'AIManager':
        """
        Configure default AI settings.
        
        Args:
            model: Default LLM model (e.g., "claude-sonnet-4-20250514")
            max_tokens: Default max tokens for responses
            temperature: Default temperature (0-1)
            
        Returns:
            Self for chaining
            
        Example:
            >>> org.ai.configure(
            ...     model="claude-sonnet-4-20250514",
            ...     max_tokens=8000,
            ...     temperature=0.5
            ... )
        """
        if model is not None:
            self._default_model = model
        if max_tokens is not None:
            self._default_max_tokens = max_tokens
        if temperature is not None:
            self._default_temperature = temperature
        return self
    
    # ========================================================================
    # Core Chat Methods
    # ========================================================================
    
    def chat(
        self,
        message: str,
        session_id: Optional[str] = None,
        context: Optional[str] = None,
        tools_enabled: bool = True,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None
    ) -> ChatResponse:
        """
        Chat with AI assistant.
        
        The AI has access to your domain's schemas as tools and can
        perform CRUD operations based on natural language requests.
        
        Args:
            message: User message
            session_id: Optional session for context continuity
            context: Optional additional context
            tools_enabled: Enable schema tools (default: True)
            model: Override default model
            max_tokens: Override default max tokens
            temperature: Override default temperature
            
        Returns:
            ChatResponse with AI response and any tool results
            
        Example:
            >>> # Simple query
            >>> response = org.ai.chat("How many active projects?")
            >>> print(response.content)
            
            >>> # With session for context
            >>> session = org.ai.sessions.create()
            >>> org.ai.chat("List projects", session_id=session.id)
            >>> org.ai.chat("Create a task for the first one", session_id=session.id)
            
            >>> # With additional context
            >>> org.ai.chat(
            ...     "Summarize this project",
            ...     context="Focus on timeline and budget"
            ... )
        """
        payload = {
            "message": message,
            "domain_name": self._domain_name,
            "tools_enabled": tools_enabled,
            "model": model or self._default_model,
            "max_tokens": max_tokens or self._default_max_tokens,
            "temperature": temperature or self._default_temperature
        }
        
        if session_id:
            payload["session_id"] = session_id
        if context:
            payload["context"] = context
        
        response = self._request("POST", "/ai/v1/chat", json=payload)
        return ChatResponse.from_dict(response)
    
    def chat_stream(
        self,
        message: str,
        session_id: Optional[str] = None,
        context: Optional[str] = None,
        tools_enabled: bool = True,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None
    ) -> Iterator[str]:
        """
        Chat with streaming response.
        
        Yields response chunks as they arrive for real-time display.
        
        Args:
            message: User message
            session_id: Optional session for context
            context: Optional additional context
            tools_enabled: Enable schema tools
            model: Override default model
            max_tokens: Override default max tokens
            temperature: Override default temperature
            
        Yields:
            Response text chunks
            
        Example:
            >>> for chunk in org.ai.chat_stream("Explain our architecture"):
            ...     print(chunk, end="", flush=True)
            >>> print()  # Final newline
        """
        payload = {
            "message": message,
            "domain_name": self._domain_name,
            "tools_enabled": tools_enabled,
            "stream": True,
            "model": model or self._default_model,
            "max_tokens": max_tokens or self._default_max_tokens,
            "temperature": temperature or self._default_temperature
        }
        
        if session_id:
            payload["session_id"] = session_id
        if context:
            payload["context"] = context
        
        # Use streaming request
        for chunk in self._stream_request("POST", "/ai/v1/chat", json=payload):
            yield chunk
    
    def ask(
        self,
        question: str,
        **kwargs
    ) -> str:
        """
        Simple question-answer (returns just the text).
        
        Convenience method that returns only the response content.
        
        Args:
            question: Question to ask
            **kwargs: Additional chat parameters
            
        Returns:
            Response text
            
        Example:
            >>> answer = org.ai.ask("How many users do we have?")
            >>> print(answer)
        """
        response = self.chat(question, **kwargs)
        return response.content
    
    # ========================================================================
    # Convenience Methods
    # ========================================================================
    
    def query(
        self,
        natural_language_query: str,
        schema: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Query data using natural language.
        
        Translates natural language to tool calls and returns results.
        
        Args:
            natural_language_query: Query in natural language
            schema: Optional schema to focus on
            
        Returns:
            Query results as list of dictionaries
            
        Example:
            >>> projects = org.ai.query("active projects with high priority")
            >>> users = org.ai.query("users created this month", schema="User")
        """
        context = f"Focus on {schema} schema." if schema else None
        
        response = self.chat(
            f"Query: {natural_language_query}. Return only the data, no explanation.",
            context=context,
            tools_enabled=True
        )
        
        # Extract tool results
        if response.tool_results:
            return response.tool_results
        
        # Try to parse response content as JSON
        try:
            return json.loads(response.content)
        except json.JSONDecodeError:
            return [{"response": response.content}]
    
    def summarize(
        self,
        data: Union[str, List[Any], Dict[str, Any]],
        format: str = "brief"
    ) -> str:
        """
        Summarize data using AI.
        
        Args:
            data: Data to summarize (string, list, or dict)
            format: Summary format ("brief", "detailed", "bullet_points")
            
        Returns:
            Summary text
            
        Example:
            >>> projects = org.Project.find(status="active")
            >>> summary = org.ai.summarize(projects, format="bullet_points")
        """
        if isinstance(data, (list, dict)):
            data_str = json.dumps(data, indent=2, default=str)
        else:
            data_str = str(data)
        
        format_instructions = {
            "brief": "Provide a brief 1-2 sentence summary.",
            "detailed": "Provide a detailed summary with key points.",
            "bullet_points": "Summarize as bullet points."
        }
        
        instruction = format_instructions.get(format, format_instructions["brief"])
        
        response = self.chat(
            f"{instruction}\n\nData:\n{data_str}",
            tools_enabled=False
        )
        return response.content
    
    def explain(
        self,
        obj: Any,
        audience: str = "technical"
    ) -> str:
        """
        Explain an object or concept.
        
        Args:
            obj: Object to explain
            audience: Target audience ("technical", "business", "simple")
            
        Returns:
            Explanation text
        """
        if hasattr(obj, 'to_dict'):
            obj_data = obj.to_dict()
        elif hasattr(obj, '__dict__'):
            obj_data = obj.__dict__
        else:
            obj_data = str(obj)
        
        audience_instructions = {
            "technical": "Explain for a technical audience with implementation details.",
            "business": "Explain for a business audience focusing on value and impact.",
            "simple": "Explain in simple terms anyone can understand."
        }
        
        instruction = audience_instructions.get(audience, audience_instructions["technical"])
        
        response = self.chat(
            f"{instruction}\n\nObject:\n{json.dumps(obj_data, indent=2, default=str)}",
            tools_enabled=False
        )
        return response.content
    
    # ========================================================================
    # Health Check
    # ========================================================================
    
    def health(self) -> Dict[str, Any]:
        """
        Check AI service health.
        
        Returns:
            Health status dictionary
        """
        return self._request("GET", "/health")
    
    def is_available(self) -> bool:
        """
        Check if AI service is available.
        
        Returns:
            True if service is responding
        """
        try:
            health = self.health()
            return health.get("status") in ["healthy", "degraded"]
        except Exception:
            return False
    
    # ========================================================================
    # Internal Methods
    # ========================================================================
    
    def _request(
        self,
        method: str,
        path: str,
        json: Dict[str, Any] = None,
        params: Dict[str, Any] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Make HTTP request to AI Service via Platform Core.
        
        All requests go through api.supero.dev which:
        1. Validates JWT
        2. Proxies to internal AI Service
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            path: API path (e.g., "/ai/v1/chat")
            json: JSON body for POST/PUT requests
            params: Query parameters for GET requests
            **kwargs: Additional request parameters
            
        Returns:
            Response JSON as dictionary
        """
        method = method.upper()
        client = self._platform_client
        
        if method == "GET":
            return client.get(path, params=params)
        elif method == "POST":
            return client.post(path, json=json)
        elif method == "PUT":
            return client.put(path, json=json)
        elif method == "DELETE":
            return client.delete(path, params=params)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")
    
    def _stream_request(
        self,
        method: str,
        path: str,
        json: Dict[str, Any] = None,
        **kwargs
    ) -> Iterator[str]:
        """
        Make streaming HTTP request to AI Service via Platform Core.
        
        Args:
            method: HTTP method
            path: API path
            json: JSON body for the request
            **kwargs: Additional request parameters
            
        Yields:
            Response content chunks
        """
        # Use stream_request from platform_client
        # Note: client.stream_request expects json_data parameter
        return self._platform_client.stream_request(method, path, json_data=json, **kwargs)


# ============================================================================
# Convenience function for standalone usage
# ============================================================================

def create_ai_manager(
    domain_name: str,
    jwt_token: str,
    platform_core_host: str = "localhost",
    platform_core_port: int = 8083
) -> AIManager:
    """
    Create standalone AI manager (without full Supero context).
    
    For use when you only need AI features.
    
    All requests go through Platform Core (api.supero.dev) which:
    1. Validates JWT
    2. Proxies AI requests to internal AI Service
    
    Args:
        domain_name: Domain name
        jwt_token: JWT authentication token
        platform_core_host: Platform Core host (default: localhost for dev)
        platform_core_port: Platform Core port (default: 8083 for dev)
        
    Returns:
        AIManager instance
        
    Example:
        >>> from supero.ai_manager import create_ai_manager
        >>> 
        >>> # Development
        >>> ai = create_ai_manager("acme-corp", jwt_token="...")
        >>> 
        >>> # Production
        >>> ai = create_ai_manager(
        ...     "acme-corp", 
        ...     jwt_token="...",
        ...     platform_core_host="api.supero.dev",
        ...     platform_core_port=443
        ... )
        >>> response = ai.chat("Hello!")
    """
    from .platform_client import PlatformClient
    
    # Single entry point - Platform Core handles everything
    platform_client = PlatformClient(
        host=platform_core_host,
        port=platform_core_port,
        jwt_token=jwt_token
    )
    
    return AIManager(
        
        platform_client=platform_client
    )
