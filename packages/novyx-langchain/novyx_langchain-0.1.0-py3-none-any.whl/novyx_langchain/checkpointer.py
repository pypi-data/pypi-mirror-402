"""
NovyxCheckpointer - LangGraph checkpoint persistence with Novyx RAM.

Provides durable state persistence for LangGraph workflows with:
- Automatic state serialization
- Multi-tenant isolation
- Semantic search over historical states
- Point-in-time recovery

Example:
    from langgraph.graph import StateGraph
    from novyx_langchain import NovyxCheckpointer

    # Create checkpointer
    checkpointer = NovyxCheckpointer(api_key="nram_tenant_xxx")

    # Build graph
    workflow = StateGraph(AgentState)
    workflow.add_node("agent", call_model)
    workflow.add_node("tools", tool_node)
    # ... configure edges

    # Compile with persistence
    graph = workflow.compile(checkpointer=checkpointer)

    # Run with thread_id for persistence
    config = {"configurable": {"thread_id": "user-123"}}
    result = graph.invoke({"messages": [HumanMessage("Hello!")]}, config)

    # State is automatically persisted to Novyx RAM
    # Resume later with same thread_id
"""

from __future__ import annotations

import json
import hashlib
import logging
from datetime import datetime, timezone
from typing import Any, Dict, Iterator, List, Optional, Tuple, Sequence
from dataclasses import dataclass

from novyx_langchain.memory import NovyxRAMClient, NovyxConfig

# LangGraph imports - v0.3+ compatible
try:
    from langgraph.checkpoint.base import (
        BaseCheckpointSaver,
        Checkpoint,
        CheckpointMetadata,
        CheckpointTuple,
        SerializerProtocol,
    )
    from langgraph.serde.jsonplus import JsonPlusSerializer
    LANGGRAPH_AVAILABLE = True
except ImportError:
    # Stub classes for when LangGraph is not installed
    LANGGRAPH_AVAILABLE = False

    class BaseCheckpointSaver:
        pass

    class Checkpoint:
        pass

    class CheckpointMetadata:
        pass

    class CheckpointTuple:
        pass

    class SerializerProtocol:
        pass

    class JsonPlusSerializer:
        pass

logger = logging.getLogger(__name__)


@dataclass
class CheckpointData:
    """Internal representation of checkpoint data."""
    thread_id: str
    checkpoint_id: str
    parent_id: Optional[str]
    checkpoint: Dict[str, Any]
    metadata: Dict[str, Any]
    created_at: str


class NovyxCheckpointer(BaseCheckpointSaver if LANGGRAPH_AVAILABLE else object):
    """
    LangGraph checkpointer using Novyx RAM for persistence.

    Features:
    - Durable state persistence across process restarts
    - Multi-tenant isolation via API key
    - Full checkpoint history with parent tracking
    - Point-in-time state recovery
    - Semantic search over checkpoint metadata

    Example:
        from langgraph.graph import StateGraph, END
        from novyx_langchain import NovyxCheckpointer

        checkpointer = NovyxCheckpointer(
            api_key="nram_tenant_xxx",
            namespace="my-agent"
        )

        # Build your graph
        builder = StateGraph(State)
        builder.add_node("agent", agent_node)
        builder.set_entry_point("agent")
        builder.add_edge("agent", END)

        # Compile with checkpointer
        graph = builder.compile(checkpointer=checkpointer)

        # Invoke with thread_id
        config = {"configurable": {"thread_id": "conv-123"}}
        result = graph.invoke({"input": "Hello"}, config)

        # State persisted! Resume anytime with same thread_id
    """

    def __init__(
        self,
        api_key: str,
        base_url: Optional[str] = None,
        namespace: str = "langgraph",
        serde: Optional[SerializerProtocol] = None,
    ):
        """
        Initialize Novyx checkpointer.

        Args:
            api_key: Novyx RAM API key
            base_url: Optional custom API URL
            namespace: Namespace for checkpoint isolation
            serde: Optional custom serializer (default: JsonPlusSerializer)
        """
        if not LANGGRAPH_AVAILABLE:
            raise ImportError(
                "LangGraph is required for NovyxCheckpointer. "
                "Install with: pip install langgraph"
            )

        super().__init__(serde=serde or JsonPlusSerializer())

        self.client = NovyxRAMClient(api_key=api_key, base_url=base_url)
        self.namespace = namespace

        # Tag prefix for checkpoints
        self._checkpoint_tag = f"checkpoint:{namespace}"

    def _thread_tag(self, thread_id: str) -> str:
        """Get tag for a specific thread."""
        return f"thread:{thread_id}"

    def _serialize_checkpoint(self, checkpoint: Checkpoint) -> str:
        """Serialize checkpoint to JSON string."""
        return self.serde.dumps(checkpoint)

    def _deserialize_checkpoint(self, data: str) -> Checkpoint:
        """Deserialize checkpoint from JSON string."""
        return self.serde.loads(data)

    def _generate_checkpoint_id(self, checkpoint: Checkpoint) -> str:
        """Generate unique checkpoint ID."""
        # Use checkpoint content hash for deduplication
        content = self._serialize_checkpoint(checkpoint)
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def put(
        self,
        config: Dict[str, Any],
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
        new_versions: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Store a checkpoint.

        Args:
            config: Configuration with thread_id
            checkpoint: The checkpoint to store
            metadata: Checkpoint metadata
            new_versions: Optional version info

        Returns:
            Updated configuration
        """
        thread_id = config["configurable"]["thread_id"]
        checkpoint_ns = config["configurable"].get("checkpoint_ns", "")

        # Get parent checkpoint ID if exists
        parent_id = config["configurable"].get("checkpoint_id")

        # Generate new checkpoint ID
        checkpoint_id = self._generate_checkpoint_id(checkpoint)

        # Serialize checkpoint
        checkpoint_data = {
            "thread_id": thread_id,
            "checkpoint_ns": checkpoint_ns,
            "checkpoint_id": checkpoint_id,
            "parent_id": parent_id,
            "checkpoint": self._serialize_checkpoint(checkpoint),
            "metadata": dict(metadata) if metadata else {},
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        if new_versions:
            checkpoint_data["versions"] = new_versions

        # Store in Novyx RAM
        self.client.store(
            observation=json.dumps(checkpoint_data),
            tags=[
                self._checkpoint_tag,
                self._thread_tag(thread_id),
                f"checkpoint_id:{checkpoint_id}",
            ],
            importance=7,  # Checkpoints are important
            agent_id="langgraph",
            metadata={
                "thread_id": thread_id,
                "checkpoint_id": checkpoint_id,
                "parent_id": parent_id,
            },
        )

        logger.debug(f"Stored checkpoint {checkpoint_id} for thread {thread_id}")

        # Return updated config
        return {
            "configurable": {
                **config["configurable"],
                "checkpoint_id": checkpoint_id,
            }
        }

    def put_writes(
        self,
        config: Dict[str, Any],
        writes: Sequence[Tuple[str, Any]],
        task_id: str,
    ) -> None:
        """
        Store intermediate writes (for parallel execution).

        Args:
            config: Configuration
            writes: List of (channel, value) tuples
            task_id: Task identifier
        """
        thread_id = config["configurable"]["thread_id"]
        checkpoint_id = config["configurable"].get("checkpoint_id", "")

        writes_data = {
            "type": "writes",
            "thread_id": thread_id,
            "checkpoint_id": checkpoint_id,
            "task_id": task_id,
            "writes": [(channel, self.serde.dumps(value)) for channel, value in writes],
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        self.client.store(
            observation=json.dumps(writes_data),
            tags=[
                self._checkpoint_tag,
                self._thread_tag(thread_id),
                f"task:{task_id}",
                "type:writes",
            ],
            importance=5,
            agent_id="langgraph",
        )

    def get_tuple(self, config: Dict[str, Any]) -> Optional[CheckpointTuple]:
        """
        Get a checkpoint tuple.

        Args:
            config: Configuration with thread_id and optional checkpoint_id

        Returns:
            CheckpointTuple or None if not found
        """
        thread_id = config["configurable"]["thread_id"]
        checkpoint_id = config["configurable"].get("checkpoint_id")

        # Build search tags
        tags = [self._checkpoint_tag, self._thread_tag(thread_id)]

        if checkpoint_id:
            tags.append(f"checkpoint_id:{checkpoint_id}")

        # Get checkpoints
        memories = self.client.list_memories(tags=tags, limit=100)

        if not memories:
            return None

        # Find the target checkpoint
        target = None
        for memory in sorted(memories, key=lambda m: m.created_at or "", reverse=True):
            try:
                data = json.loads(memory.observation)
                if data.get("type") == "writes":
                    continue  # Skip write records

                if checkpoint_id:
                    if data.get("checkpoint_id") == checkpoint_id:
                        target = data
                        break
                else:
                    # Return most recent
                    target = data
                    break
            except json.JSONDecodeError:
                continue

        if not target:
            return None

        # Deserialize checkpoint
        checkpoint = self._deserialize_checkpoint(target["checkpoint"])
        metadata = CheckpointMetadata(**target.get("metadata", {}))

        # Get pending writes for this checkpoint
        pending_writes = self._get_pending_writes(thread_id, target["checkpoint_id"])

        return CheckpointTuple(
            config={
                "configurable": {
                    "thread_id": thread_id,
                    "checkpoint_ns": target.get("checkpoint_ns", ""),
                    "checkpoint_id": target["checkpoint_id"],
                }
            },
            checkpoint=checkpoint,
            metadata=metadata,
            parent_config={
                "configurable": {
                    "thread_id": thread_id,
                    "checkpoint_ns": target.get("checkpoint_ns", ""),
                    "checkpoint_id": target.get("parent_id"),
                }
            } if target.get("parent_id") else None,
            pending_writes=pending_writes,
        )

    def _get_pending_writes(
        self,
        thread_id: str,
        checkpoint_id: str,
    ) -> List[Tuple[str, str, Any]]:
        """Get pending writes for a checkpoint."""
        tags = [
            self._checkpoint_tag,
            self._thread_tag(thread_id),
            "type:writes",
        ]

        memories = self.client.list_memories(tags=tags, limit=100)
        pending = []

        for memory in memories:
            try:
                data = json.loads(memory.observation)
                if data.get("checkpoint_id") == checkpoint_id:
                    for channel, value_str in data.get("writes", []):
                        value = self.serde.loads(value_str)
                        pending.append((data["task_id"], channel, value))
            except (json.JSONDecodeError, KeyError):
                continue

        return pending

    def list(
        self,
        config: Optional[Dict[str, Any]] = None,
        *,
        filter: Optional[Dict[str, Any]] = None,
        before: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None,
    ) -> Iterator[CheckpointTuple]:
        """
        List checkpoints.

        Args:
            config: Optional config to filter by thread_id
            filter: Optional metadata filter
            before: Return checkpoints before this config
            limit: Maximum number to return

        Yields:
            CheckpointTuple for each matching checkpoint
        """
        tags = [self._checkpoint_tag]

        if config:
            thread_id = config["configurable"].get("thread_id")
            if thread_id:
                tags.append(self._thread_tag(thread_id))

        memories = self.client.list_memories(tags=tags, limit=limit or 100)

        # Sort by created_at descending
        memories = sorted(memories, key=lambda m: m.created_at or "", reverse=True)

        before_ts = None
        if before:
            before_checkpoint_id = before["configurable"].get("checkpoint_id")
            # Find the before checkpoint to get its timestamp
            for memory in memories:
                try:
                    data = json.loads(memory.observation)
                    if data.get("checkpoint_id") == before_checkpoint_id:
                        before_ts = data.get("created_at")
                        break
                except json.JSONDecodeError:
                    continue

        count = 0
        for memory in memories:
            try:
                data = json.loads(memory.observation)

                if data.get("type") == "writes":
                    continue

                # Apply before filter
                if before_ts and data.get("created_at", "") >= before_ts:
                    continue

                # Apply metadata filter
                if filter:
                    metadata = data.get("metadata", {})
                    if not all(metadata.get(k) == v for k, v in filter.items()):
                        continue

                # Deserialize
                checkpoint = self._deserialize_checkpoint(data["checkpoint"])
                metadata_obj = CheckpointMetadata(**data.get("metadata", {}))

                yield CheckpointTuple(
                    config={
                        "configurable": {
                            "thread_id": data["thread_id"],
                            "checkpoint_ns": data.get("checkpoint_ns", ""),
                            "checkpoint_id": data["checkpoint_id"],
                        }
                    },
                    checkpoint=checkpoint,
                    metadata=metadata_obj,
                    parent_config={
                        "configurable": {
                            "thread_id": data["thread_id"],
                            "checkpoint_ns": data.get("checkpoint_ns", ""),
                            "checkpoint_id": data.get("parent_id"),
                        }
                    } if data.get("parent_id") else None,
                )

                count += 1
                if limit and count >= limit:
                    break

            except (json.JSONDecodeError, KeyError) as e:
                logger.warning(f"Failed to parse checkpoint: {e}")
                continue

    async def aget_tuple(self, config: Dict[str, Any]) -> Optional[CheckpointTuple]:
        """Async version of get_tuple."""
        # For now, use sync version (could add async client later)
        return self.get_tuple(config)

    async def aput(
        self,
        config: Dict[str, Any],
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
        new_versions: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Async version of put."""
        return self.put(config, checkpoint, metadata, new_versions)

    async def aput_writes(
        self,
        config: Dict[str, Any],
        writes: Sequence[Tuple[str, Any]],
        task_id: str,
    ) -> None:
        """Async version of put_writes."""
        return self.put_writes(config, writes, task_id)

    async def alist(
        self,
        config: Optional[Dict[str, Any]] = None,
        *,
        filter: Optional[Dict[str, Any]] = None,
        before: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None,
    ) -> Iterator[CheckpointTuple]:
        """Async version of list."""
        for item in self.list(config, filter=filter, before=before, limit=limit):
            yield item

    def clear_thread(self, thread_id: str) -> int:
        """
        Clear all checkpoints for a thread.

        Args:
            thread_id: Thread to clear

        Returns:
            Number of checkpoints deleted
        """
        return self.client.clear_all(
            tags=[self._checkpoint_tag, self._thread_tag(thread_id)]
        )

    def get_thread_history(
        self,
        thread_id: str,
        limit: int = 50,
    ) -> List[CheckpointData]:
        """
        Get checkpoint history for a thread.

        Args:
            thread_id: Thread identifier
            limit: Maximum checkpoints to return

        Returns:
            List of CheckpointData in reverse chronological order
        """
        tags = [self._checkpoint_tag, self._thread_tag(thread_id)]
        memories = self.client.list_memories(tags=tags, limit=limit)

        history = []
        for memory in sorted(memories, key=lambda m: m.created_at or "", reverse=True):
            try:
                data = json.loads(memory.observation)
                if data.get("type") == "writes":
                    continue

                history.append(CheckpointData(
                    thread_id=data["thread_id"],
                    checkpoint_id=data["checkpoint_id"],
                    parent_id=data.get("parent_id"),
                    checkpoint=json.loads(data["checkpoint"]),
                    metadata=data.get("metadata", {}),
                    created_at=data.get("created_at", ""),
                ))
            except (json.JSONDecodeError, KeyError):
                continue

        return history
