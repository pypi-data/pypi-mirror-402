"""
NovyxBufferedMemory - Local buffer with periodic flush to Novyx RAM.

For high-throughput scenarios where you want to batch writes to reduce
API calls while maintaining local responsiveness.

Example:
    from novyx_langchain import NovyxBufferedMemory

    memory = NovyxBufferedMemory(
        api_key="nram_tenant_xxx",
        session_id="user-123",
        buffer_size=50,      # Flush after 50 messages
        flush_interval=30,   # Or flush every 30 seconds
    )

    # Messages are buffered locally and flushed periodically
    chain = ConversationChain(llm=llm, memory=memory)
"""

from __future__ import annotations

import json
import logging
import threading
import time
from collections import deque
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Sequence
from dataclasses import dataclass, field

from pydantic import Field

from novyx_langchain.memory import (
    NovyxMemory,
    NovyxRAMClient,
    NovyxChatMessageHistory,
)

try:
    from langchain_core.messages import (
        BaseMessage,
        HumanMessage,
        AIMessage,
        SystemMessage,
    )
except ImportError:
    from langchain.schema import (
        BaseMessage,
        HumanMessage,
        AIMessage,
        SystemMessage,
    )

logger = logging.getLogger(__name__)


@dataclass
class BufferedMessage:
    """A message waiting in the buffer."""
    message: BaseMessage
    timestamp: str
    importance: int = 5
    tags: List[str] = field(default_factory=list)


class MessageBuffer:
    """
    Thread-safe message buffer with automatic flushing.

    Buffers messages locally and flushes to Novyx RAM when:
    - Buffer reaches max size
    - Flush interval elapsed
    - Manual flush() called
    """

    def __init__(
        self,
        client: NovyxRAMClient,
        session_id: str,
        agent_id: str = "langchain",
        max_size: int = 50,
        flush_interval: float = 30.0,
        auto_start: bool = True,
    ):
        """
        Initialize message buffer.

        Args:
            client: Novyx RAM client
            session_id: Session identifier
            agent_id: Agent identifier
            max_size: Max messages before auto-flush
            flush_interval: Seconds between auto-flush
            auto_start: Start background flush thread
        """
        self.client = client
        self.session_id = session_id
        self.agent_id = agent_id
        self.max_size = max_size
        self.flush_interval = flush_interval

        self._buffer: deque[BufferedMessage] = deque()
        self._lock = threading.Lock()
        self._last_flush = time.time()

        # Background flush thread
        self._running = False
        self._flush_thread: Optional[threading.Thread] = None

        if auto_start:
            self.start()

    def start(self) -> None:
        """Start background flush thread."""
        if self._running:
            return

        self._running = True
        self._flush_thread = threading.Thread(
            target=self._flush_loop,
            daemon=True,
            name="NovyxBufferFlush",
        )
        self._flush_thread.start()

    def stop(self) -> None:
        """Stop background flush thread and flush remaining."""
        self._running = False
        if self._flush_thread:
            self._flush_thread.join(timeout=5.0)
        self.flush()

    def _flush_loop(self) -> None:
        """Background loop for periodic flushing."""
        while self._running:
            time.sleep(1.0)

            # Check if flush needed
            elapsed = time.time() - self._last_flush
            if elapsed >= self.flush_interval:
                self.flush()

    def add(self, message: BaseMessage, importance: int = 5, tags: Optional[List[str]] = None) -> None:
        """
        Add a message to the buffer.

        Args:
            message: Message to buffer
            importance: Message importance (1-10)
            tags: Optional additional tags
        """
        buffered = BufferedMessage(
            message=message,
            timestamp=datetime.now(timezone.utc).isoformat(),
            importance=importance,
            tags=tags or [],
        )

        with self._lock:
            self._buffer.append(buffered)

            # Auto-flush if buffer full
            if len(self._buffer) >= self.max_size:
                self._do_flush()

    def flush(self) -> int:
        """
        Flush buffer to Novyx RAM.

        Returns:
            Number of messages flushed
        """
        with self._lock:
            return self._do_flush()

    def _do_flush(self) -> int:
        """Internal flush (must hold lock)."""
        if not self._buffer:
            return 0

        count = 0
        session_tag = f"session:{self.session_id}"
        message_tag = "chat:message"

        while self._buffer:
            buffered = self._buffer.popleft()

            try:
                # Convert message to observation
                msg_type = "human"
                if isinstance(buffered.message, AIMessage):
                    msg_type = "ai"
                elif isinstance(buffered.message, SystemMessage):
                    msg_type = "system"

                observation = json.dumps({
                    "type": msg_type,
                    "content": buffered.message.content,
                    "buffered_at": buffered.timestamp,
                })

                # Store in Novyx RAM
                self.client.store(
                    observation=observation,
                    tags=[session_tag, message_tag] + buffered.tags,
                    importance=buffered.importance,
                    agent_id=self.agent_id,
                    metadata={
                        "session_id": self.session_id,
                        "buffered": True,
                    },
                )
                count += 1

            except Exception as e:
                logger.error(f"Failed to flush message: {e}")
                # Re-add to buffer for retry
                self._buffer.appendleft(buffered)
                break

        self._last_flush = time.time()
        logger.debug(f"Flushed {count} messages to Novyx RAM")
        return count

    def get_local_messages(self) -> List[BaseMessage]:
        """Get messages currently in buffer (not yet flushed)."""
        with self._lock:
            return [b.message for b in self._buffer]

    def clear_local(self) -> int:
        """Clear local buffer without flushing."""
        with self._lock:
            count = len(self._buffer)
            self._buffer.clear()
            return count

    def __len__(self) -> int:
        """Number of messages in buffer."""
        with self._lock:
            return len(self._buffer)

    def __del__(self):
        """Cleanup on destruction."""
        self.stop()


class BufferedChatMessageHistory(NovyxChatMessageHistory):
    """
    Chat message history with local buffering.

    Messages are buffered locally for fast access and periodically
    flushed to Novyx RAM.
    """

    def __init__(
        self,
        api_key: str,
        session_id: str,
        base_url: Optional[str] = None,
        agent_id: Optional[str] = None,
        max_messages: int = 100,
        buffer_size: int = 50,
        flush_interval: float = 30.0,
    ):
        """
        Initialize buffered chat history.

        Args:
            api_key: Novyx RAM API key
            session_id: Session identifier
            base_url: Optional custom API URL
            agent_id: Agent identifier
            max_messages: Max messages to retrieve from remote
            buffer_size: Local buffer size before flush
            flush_interval: Seconds between auto-flush
        """
        super().__init__(
            api_key=api_key,
            session_id=session_id,
            base_url=base_url,
            agent_id=agent_id,
            max_messages=max_messages,
        )

        # Initialize buffer
        self._buffer = MessageBuffer(
            client=self.client,
            session_id=session_id,
            agent_id=agent_id or "langchain",
            max_size=buffer_size,
            flush_interval=flush_interval,
        )

    @property
    def messages(self) -> List[BaseMessage]:
        """Get all messages (remote + local buffer)."""
        # Get remote messages
        remote_messages = super().messages

        # Add local buffered messages
        local_messages = self._buffer.get_local_messages()

        return remote_messages + local_messages

    def add_message(self, message: BaseMessage) -> None:
        """Add message to local buffer."""
        importance = 5
        if isinstance(message, SystemMessage):
            importance = 8
        elif isinstance(message, AIMessage):
            importance = 6

        self._buffer.add(message, importance=importance)

    def add_messages(self, messages: Sequence[BaseMessage]) -> None:
        """Add multiple messages to buffer."""
        for message in messages:
            self.add_message(message)

    def flush(self) -> int:
        """Flush buffer to Novyx RAM."""
        return self._buffer.flush()

    def clear(self) -> None:
        """Clear all messages (remote and local)."""
        self._buffer.clear_local()
        super().clear()

    def __del__(self):
        """Ensure buffer is flushed on cleanup."""
        if hasattr(self, '_buffer'):
            self._buffer.stop()


class NovyxBufferedMemory(NovyxMemory):
    """
    Memory with local buffering for high-throughput scenarios.

    Messages are buffered locally and periodically flushed to Novyx RAM.
    This reduces API calls while maintaining responsiveness.

    Example:
        memory = NovyxBufferedMemory(
            api_key="nram_tenant_xxx",
            session_id="user-123",
            buffer_size=50,      # Flush after 50 messages
            flush_interval=30,   # Or every 30 seconds
        )

        chain = ConversationChain(llm=llm, memory=memory)

        # Messages buffered locally, flushed to RAM periodically
        for i in range(100):
            response = chain.invoke({"input": f"Message {i}"})

        # Force flush
        memory.flush()
    """

    # Buffer settings
    buffer_size: int = Field(50, description="Max messages before auto-flush")
    flush_interval: float = Field(30.0, description="Seconds between auto-flush")

    _buffered_history: Optional[BufferedChatMessageHistory] = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Override with buffered chat history
        self._buffered_history = BufferedChatMessageHistory(
            api_key=self.api_key,
            session_id=self.session_id,
            base_url=self.base_url,
            agent_id=self.agent_id,
            buffer_size=self.buffer_size,
            flush_interval=self.flush_interval,
        )
        self._chat_history = self._buffered_history

    def flush(self) -> int:
        """
        Flush local buffer to Novyx RAM.

        Returns:
            Number of messages flushed
        """
        if self._buffered_history:
            return self._buffered_history.flush()
        return 0

    def get_buffer_size(self) -> int:
        """Get current number of buffered messages."""
        if self._buffered_history and hasattr(self._buffered_history, '_buffer'):
            return len(self._buffered_history._buffer)
        return 0

    def save_context(self, inputs: Dict[str, Any], outputs: Dict[str, str]) -> None:
        """Save context (buffered)."""
        super().save_context(inputs, outputs)

    def clear(self) -> None:
        """Clear memory (flushes buffer first)."""
        self.flush()
        super().clear()

    def __del__(self):
        """Ensure buffer is flushed on cleanup."""
        try:
            self.flush()
        except Exception:
            pass
