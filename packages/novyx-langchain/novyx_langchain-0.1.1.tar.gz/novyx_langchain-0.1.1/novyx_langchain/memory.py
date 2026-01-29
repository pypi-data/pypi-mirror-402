"""
NovyxMemory - Persistent semantic memory for LangChain agents.

This module provides:
- NovyxRAMClient: Low-level HTTP client for Novyx RAM API
- NovyxChatMessageHistory: BaseChatMessageHistory implementation
- NovyxMemory: Full ConversationBufferMemory-compatible class

Example:
    from novyx_langchain import NovyxMemory
    from langchain.chains import ConversationChain
    from langchain_openai import ChatOpenAI

    memory = NovyxMemory(
        api_key="nram_tenant_xxx",
        session_id="user-123",
        k=10  # Retrieve last 10 relevant messages
    )

    chain = ConversationChain(
        llm=ChatOpenAI(),
        memory=memory
    )

    response = chain.invoke({"input": "Hello!"})
"""

from __future__ import annotations

import json
import logging
import time
import hashlib
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Sequence, Union
from dataclasses import dataclass, field

import requests
from pydantic import BaseModel, Field

# LangChain imports - compatible with v0.3+
try:
    from langchain_core.chat_history import BaseChatMessageHistory
    from langchain_core.messages import (
        AIMessage,
        BaseMessage,
        HumanMessage,
        SystemMessage,
        messages_from_dict,
        messages_to_dict,
    )
    from langchain_core.memory import BaseMemory
except ImportError:
    # Fallback for older versions
    from langchain.schema import (
        BaseChatMessageHistory,
        BaseMessage,
        AIMessage,
        HumanMessage,
        SystemMessage,
    )
    from langchain.memory import BaseMemory
    messages_from_dict = None
    messages_to_dict = None

logger = logging.getLogger(__name__)


# =============================================================================
# Configuration
# =============================================================================

DEFAULT_BASE_URL = "https://novyx-ram-api.fly.dev/v1"
DEFAULT_TIMEOUT = 30
DEFAULT_MAX_RETRIES = 3
DEFAULT_RETRY_DELAY = 1.0


@dataclass
class NovyxConfig:
    """Configuration for Novyx RAM client."""
    base_url: str = DEFAULT_BASE_URL
    timeout: int = DEFAULT_TIMEOUT
    max_retries: int = DEFAULT_MAX_RETRIES
    retry_delay: float = DEFAULT_RETRY_DELAY
    conflict_strategy: str = "lww"  # last-writer-wins


# =============================================================================
# Data Models
# =============================================================================

class MemoryItem(BaseModel):
    """A single memory item from Novyx RAM."""
    id: str
    observation: str
    tags: List[str] = Field(default_factory=list)
    importance: int = 5
    confidence: float = 1.0
    created_at: Optional[str] = None
    agent_id: Optional[str] = None
    context_ids: List[str] = Field(default_factory=list)
    score: Optional[float] = None  # Relevance score from search


class SearchResult(BaseModel):
    """Search result from semantic query."""
    memories: List[MemoryItem]
    query: str
    total_count: int


# =============================================================================
# HTTP Client
# =============================================================================

class NovyxRAMClient:
    """
    Low-level HTTP client for Novyx RAM API.

    Handles authentication, retries, and error handling.

    Example:
        client = NovyxRAMClient(api_key="nram_tenant_xxx")

        # Store a memory
        memory_id = client.store(
            observation="User prefers dark mode",
            tags=["preferences", "ui"],
            importance=7
        )

        # Semantic search
        results = client.search("What are user preferences?", limit=5)

        # List all memories
        memories = client.list_memories(tags=["preferences"])
    """

    def __init__(
        self,
        api_key: str,
        base_url: Optional[str] = None,
        config: Optional[NovyxConfig] = None,
    ):
        """
        Initialize Novyx RAM client.

        Args:
            api_key: API key in format "nram_{tenant_id}_{signature}"
            base_url: Optional custom base URL
            config: Optional configuration object
        """
        self.api_key = api_key
        self.config = config or NovyxConfig()
        self.base_url = (base_url or self.config.base_url).rstrip("/")

        # Extract tenant ID from API key
        self.tenant_id = self._extract_tenant_id(api_key)

        # Session for connection pooling
        self._session = requests.Session()
        self._session.headers.update({
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "novyx-langchain/0.1.0",
        })

    def _extract_tenant_id(self, api_key: str) -> str:
        """Extract tenant ID from API key."""
        if api_key.startswith("nram_"):
            parts = api_key.split("_")
            if len(parts) >= 2:
                return parts[1]
        return "default"

    def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None,
    ) -> Dict:
        """Make HTTP request with retry logic."""
        url = f"{self.base_url}{endpoint}"

        for attempt in range(self.config.max_retries):
            try:
                response = self._session.request(
                    method=method,
                    url=url,
                    json=data,
                    params=params,
                    timeout=self.config.timeout,
                )

                if response.status_code == 429:
                    # Rate limited - wait and retry
                    retry_after = int(response.headers.get("Retry-After", 60))
                    logger.warning(f"Rate limited, waiting {retry_after}s")
                    time.sleep(min(retry_after, 60))
                    continue

                if response.status_code == 409:
                    # Conflict - handle based on strategy
                    logger.warning(f"Conflict detected: {response.json()}")
                    if self.config.conflict_strategy == "lww":
                        # Retry with force flag
                        if data:
                            data["force"] = True
                        continue
                    raise ConflictError(response.json())

                response.raise_for_status()
                return response.json()

            except requests.exceptions.Timeout:
                logger.warning(f"Request timeout (attempt {attempt + 1})")
                if attempt < self.config.max_retries - 1:
                    time.sleep(self.config.retry_delay * (attempt + 1))
                else:
                    raise

            except requests.exceptions.RequestException as e:
                logger.error(f"Request failed: {e}")
                if attempt < self.config.max_retries - 1:
                    time.sleep(self.config.retry_delay * (attempt + 1))
                else:
                    raise

        raise RuntimeError("Max retries exceeded")

    def store(
        self,
        observation: str,
        tags: Optional[List[str]] = None,
        importance: int = 5,
        confidence: float = 1.0,
        context_ids: Optional[List[str]] = None,
        agent_id: Optional[str] = None,
        metadata: Optional[Dict] = None,
    ) -> str:
        """
        Store a memory in Novyx RAM.

        Args:
            observation: The memory content
            tags: Optional tags for categorization
            importance: Importance level 1-10 (default 5)
            confidence: Confidence score 0-1 (default 1.0)
            context_ids: Optional related memory IDs
            agent_id: Optional agent identifier
            metadata: Optional additional metadata

        Returns:
            Memory ID
        """
        data = {
            "observation": observation,
            "tags": tags or [],
            "importance": importance,
            "confidence": confidence,
        }

        if context_ids:
            data["context_ids"] = context_ids
        if agent_id:
            data["agent_id"] = agent_id
        if metadata:
            data["metadata"] = metadata

        result = self._request("POST", "/memories", data=data)
        return result.get("id", result.get("memory_id", ""))

    def search(
        self,
        query: str,
        limit: int = 5,
        min_score: float = 0.0,
        tags: Optional[List[str]] = None,
    ) -> List[MemoryItem]:
        """
        Semantic search for memories.

        Args:
            query: Search query
            limit: Maximum results
            min_score: Minimum relevance score
            tags: Optional tag filter

        Returns:
            List of matching memories sorted by relevance
        """
        params = {
            "query": query,
            "limit": limit,
            "min_score": min_score,
        }
        if tags:
            params["tags"] = ",".join(tags)

        result = self._request("GET", "/memories/search", params=params)

        memories = []
        for item in result.get("memories", result.get("results", [])):
            memories.append(MemoryItem(
                id=item.get("id", ""),
                observation=item.get("observation", item.get("content", "")),
                tags=item.get("tags", []),
                importance=item.get("importance", 5),
                confidence=item.get("confidence", 1.0),
                created_at=item.get("created_at"),
                agent_id=item.get("agent_id"),
                context_ids=item.get("context_ids", []),
                score=item.get("score", item.get("relevance", 0.0)),
            ))

        return memories

    def list_memories(
        self,
        tags: Optional[List[str]] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[MemoryItem]:
        """
        List memories with optional filtering.

        Args:
            tags: Optional tag filter
            limit: Maximum results
            offset: Pagination offset

        Returns:
            List of memories
        """
        params = {"limit": limit, "offset": offset}
        if tags:
            params["tags"] = ",".join(tags)

        result = self._request("GET", "/memories", params=params)

        memories = []
        for item in result.get("memories", []):
            memories.append(MemoryItem(
                id=item.get("id", ""),
                observation=item.get("observation", item.get("content", "")),
                tags=item.get("tags", []),
                importance=item.get("importance", 5),
                confidence=item.get("confidence", 1.0),
                created_at=item.get("created_at"),
                agent_id=item.get("agent_id"),
                context_ids=item.get("context_ids", []),
            ))

        return memories

    def get_memory(self, memory_id: str) -> Optional[MemoryItem]:
        """Get a specific memory by ID."""
        try:
            result = self._request("GET", f"/memories/{memory_id}")
            return MemoryItem(
                id=result.get("id", memory_id),
                observation=result.get("observation", result.get("content", "")),
                tags=result.get("tags", []),
                importance=result.get("importance", 5),
                confidence=result.get("confidence", 1.0),
                created_at=result.get("created_at"),
                agent_id=result.get("agent_id"),
                context_ids=result.get("context_ids", []),
            )
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                return None
            raise

    def delete_memory(self, memory_id: str) -> bool:
        """Delete a memory by ID."""
        try:
            self._request("DELETE", f"/memories/{memory_id}")
            return True
        except requests.exceptions.HTTPError:
            return False

    def get_stats(self) -> Dict:
        """Get memory statistics."""
        return self._request("GET", "/memories/stats")

    def clear_all(self, tags: Optional[List[str]] = None) -> int:
        """
        Clear all memories (optionally filtered by tags).

        WARNING: This is destructive!

        Args:
            tags: Optional tag filter (only delete matching)

        Returns:
            Number of memories deleted
        """
        memories = self.list_memories(tags=tags, limit=1000)
        count = 0

        for memory in memories:
            if self.delete_memory(memory.id):
                count += 1

        return count


class ConflictError(Exception):
    """Raised when a write conflict occurs."""
    pass


# =============================================================================
# LangChain Chat Message History
# =============================================================================

class NovyxChatMessageHistory(BaseChatMessageHistory):
    """
    Chat message history backed by Novyx RAM.

    Implements BaseChatMessageHistory for use with RunnableWithMessageHistory.

    Example:
        from langchain_core.runnables.history import RunnableWithMessageHistory

        def get_session_history(session_id: str) -> BaseChatMessageHistory:
            return NovyxChatMessageHistory(
                api_key="nram_tenant_xxx",
                session_id=session_id
            )

        chain_with_history = RunnableWithMessageHistory(
            chain,
            get_session_history,
            input_messages_key="input",
            history_messages_key="history",
        )
    """

    def __init__(
        self,
        api_key: str,
        session_id: str,
        base_url: Optional[str] = None,
        agent_id: Optional[str] = None,
        max_messages: int = 100,
    ):
        """
        Initialize chat message history.

        Args:
            api_key: Novyx RAM API key
            session_id: Unique session/thread identifier
            base_url: Optional custom API URL
            agent_id: Optional agent identifier
            max_messages: Maximum messages to retrieve
        """
        self.client = NovyxRAMClient(api_key=api_key, base_url=base_url)
        self.session_id = session_id
        self.agent_id = agent_id or "langchain"
        self.max_messages = max_messages

        # Tag for this session's messages
        self._session_tag = f"session:{session_id}"
        self._message_tag = "chat:message"

    @property
    def messages(self) -> List[BaseMessage]:
        """Retrieve all messages for this session."""
        memories = self.client.list_memories(
            tags=[self._session_tag, self._message_tag],
            limit=self.max_messages,
        )

        messages = []
        for memory in sorted(memories, key=lambda m: m.created_at or ""):
            msg = self._memory_to_message(memory)
            if msg:
                messages.append(msg)

        return messages

    def _memory_to_message(self, memory: MemoryItem) -> Optional[BaseMessage]:
        """Convert a memory item to a LangChain message."""
        try:
            # Parse stored message data
            data = json.loads(memory.observation)
            msg_type = data.get("type", "human")
            content = data.get("content", "")

            if msg_type == "human":
                return HumanMessage(content=content)
            elif msg_type == "ai":
                return AIMessage(content=content)
            elif msg_type == "system":
                return SystemMessage(content=content)
            else:
                return HumanMessage(content=content)
        except json.JSONDecodeError:
            # Fallback: treat as human message
            return HumanMessage(content=memory.observation)

    def _message_to_observation(self, message: BaseMessage) -> str:
        """Convert a LangChain message to observation string."""
        msg_type = "human"
        if isinstance(message, AIMessage):
            msg_type = "ai"
        elif isinstance(message, SystemMessage):
            msg_type = "system"

        return json.dumps({
            "type": msg_type,
            "content": message.content,
        })

    def add_message(self, message: BaseMessage) -> None:
        """Add a message to the history."""
        observation = self._message_to_observation(message)

        # Determine importance based on message type
        importance = 5
        if isinstance(message, SystemMessage):
            importance = 8
        elif isinstance(message, AIMessage):
            importance = 6

        self.client.store(
            observation=observation,
            tags=[self._session_tag, self._message_tag],
            importance=importance,
            agent_id=self.agent_id,
            metadata={
                "session_id": self.session_id,
                "message_type": type(message).__name__,
            },
        )

    def add_messages(self, messages: Sequence[BaseMessage]) -> None:
        """Add multiple messages."""
        for message in messages:
            self.add_message(message)

    def clear(self) -> None:
        """Clear all messages for this session."""
        self.client.clear_all(tags=[self._session_tag])


# =============================================================================
# Full Memory Class (ConversationBufferMemory compatible)
# =============================================================================

class NovyxMemory(BaseMemory):
    """
    Full-featured memory class compatible with LangChain's ConversationBufferMemory.

    Provides semantic retrieval of relevant context based on the current input,
    rather than just returning recent messages.

    Example:
        from novyx_langchain import NovyxMemory
        from langchain.chains import ConversationChain

        memory = NovyxMemory(
            api_key="nram_tenant_xxx",
            session_id="user-123",
            k=10,  # Retrieve top 10 relevant memories
            return_messages=True
        )

        chain = ConversationChain(llm=llm, memory=memory)

    For AgentExecutor:
        from langchain.agents import AgentExecutor

        agent_executor = AgentExecutor(
            agent=agent,
            tools=tools,
            memory=memory,
            verbose=True
        )
    """

    # Pydantic fields
    api_key: str = Field(..., description="Novyx RAM API key")
    session_id: str = Field(..., description="Session/thread identifier")
    base_url: Optional[str] = Field(None, description="Custom API URL")
    agent_id: str = Field("langchain", description="Agent identifier")

    # Memory settings
    k: int = Field(10, description="Number of memories to retrieve")
    memory_key: str = Field("history", description="Key for memory in chain")
    input_key: str = Field("input", description="Key for input in chain")
    output_key: str = Field("output", description="Key for output in chain")
    human_prefix: str = Field("Human", description="Prefix for human messages")
    ai_prefix: str = Field("AI", description="Prefix for AI messages")
    return_messages: bool = Field(False, description="Return Message objects vs string")

    # Semantic search settings
    semantic_search: bool = Field(True, description="Use semantic search for retrieval")
    min_relevance: float = Field(0.3, description="Minimum relevance score")
    include_recent: int = Field(3, description="Always include N most recent messages")

    # Internal
    _client: Optional[NovyxRAMClient] = None
    _chat_history: Optional[NovyxChatMessageHistory] = None

    class Config:
        arbitrary_types_allowed = True
        underscore_attrs_are_private = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._client = NovyxRAMClient(
            api_key=self.api_key,
            base_url=self.base_url,
        )
        self._chat_history = NovyxChatMessageHistory(
            api_key=self.api_key,
            session_id=self.session_id,
            base_url=self.base_url,
            agent_id=self.agent_id,
        )

    @property
    def memory_variables(self) -> List[str]:
        """Return memory variables."""
        return [self.memory_key]

    def load_memory_variables(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Load relevant memories based on input.

        Uses semantic search to find the most relevant memories,
        plus always includes the most recent messages for context.
        """
        # Get the input to search for
        input_text = inputs.get(self.input_key, "")
        if not input_text and inputs:
            # Try to find any string input
            input_text = str(list(inputs.values())[0])

        messages = []

        if self.semantic_search and input_text:
            # Semantic search for relevant memories
            relevant = self._client.search(
                query=input_text,
                limit=self.k,
                min_score=self.min_relevance,
                tags=[f"session:{self.session_id}"],
            )

            for memory in relevant:
                msg = self._memory_to_message(memory)
                if msg:
                    messages.append(msg)

        # Always include recent messages for immediate context
        if self.include_recent > 0:
            recent = self._chat_history.messages[-self.include_recent:]
            for msg in recent:
                if msg not in messages:
                    messages.append(msg)

        # Sort by some order (could improve this)
        # For now, keep semantic results first, then recent

        if self.return_messages:
            return {self.memory_key: messages}
        else:
            # Format as string
            buffer = self._format_messages(messages)
            return {self.memory_key: buffer}

    def _memory_to_message(self, memory: MemoryItem) -> Optional[BaseMessage]:
        """Convert memory to message."""
        try:
            data = json.loads(memory.observation)
            msg_type = data.get("type", "human")
            content = data.get("content", "")

            if msg_type == "human":
                return HumanMessage(content=content)
            elif msg_type == "ai":
                return AIMessage(content=content)
            elif msg_type == "system":
                return SystemMessage(content=content)
            return HumanMessage(content=content)
        except json.JSONDecodeError:
            return HumanMessage(content=memory.observation)

    def _format_messages(self, messages: List[BaseMessage]) -> str:
        """Format messages as string."""
        lines = []
        for msg in messages:
            if isinstance(msg, HumanMessage):
                lines.append(f"{self.human_prefix}: {msg.content}")
            elif isinstance(msg, AIMessage):
                lines.append(f"{self.ai_prefix}: {msg.content}")
            elif isinstance(msg, SystemMessage):
                lines.append(f"System: {msg.content}")
            else:
                lines.append(str(msg.content))
        return "\n".join(lines)

    def save_context(self, inputs: Dict[str, Any], outputs: Dict[str, str]) -> None:
        """
        Save context from this conversation turn.

        Args:
            inputs: Input from the user
            outputs: Output from the AI
        """
        input_text = inputs.get(self.input_key, "")
        output_text = outputs.get(self.output_key, "")

        if input_text:
            self._chat_history.add_message(HumanMessage(content=input_text))

        if output_text:
            self._chat_history.add_message(AIMessage(content=output_text))

    def clear(self) -> None:
        """Clear memory for this session."""
        self._chat_history.clear()

    # Convenience methods

    def add_user_message(self, content: str) -> None:
        """Add a user message."""
        self._chat_history.add_message(HumanMessage(content=content))

    def add_ai_message(self, content: str) -> None:
        """Add an AI message."""
        self._chat_history.add_message(AIMessage(content=content))

    def add_system_message(self, content: str) -> None:
        """Add a system message."""
        self._chat_history.add_message(SystemMessage(content=content))

    def search(self, query: str, limit: int = 5) -> List[MemoryItem]:
        """Search memories semantically."""
        return self._client.search(
            query=query,
            limit=limit,
            tags=[f"session:{self.session_id}"],
        )

    def store_memory(
        self,
        content: str,
        tags: Optional[List[str]] = None,
        importance: int = 5,
    ) -> str:
        """Store a custom memory (not a chat message)."""
        all_tags = [f"session:{self.session_id}", "custom:memory"]
        if tags:
            all_tags.extend(tags)

        return self._client.store(
            observation=content,
            tags=all_tags,
            importance=importance,
            agent_id=self.agent_id,
        )
