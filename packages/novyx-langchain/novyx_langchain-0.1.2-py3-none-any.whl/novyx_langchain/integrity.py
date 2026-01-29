"""
NovyxIntegrityMemory - Tamper-proof memory with cryptographic verification.

This module provides memory classes that integrate with Novyx Integrity
for verified, tamper-proof writes. Every memory operation goes through
challenge-response authentication.

This makes Novyx the ONLY LangChain memory provider with tamper-proof writes.

Example:
    from novyx_langchain import NovyxIntegrityMemory

    memory = NovyxIntegrityMemory(
        api_key="nram_tenant_xxx",           # Novyx RAM API key
        integrity_api_key="int_xxx",          # Novyx Integrity API key
        integrity_secret="shared_secret",     # Shared secret for challenges
        session_id="user-123"
    )

    # Use with LangChain - all writes are cryptographically verified
    chain = ConversationChain(llm=llm, memory=memory)
"""

from __future__ import annotations

import hmac
import hashlib
import json
import logging
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Callable, TypeVar
from functools import wraps

import requests
from pydantic import Field

from novyx_langchain.memory import (
    NovyxMemory,
    NovyxChatMessageHistory,
    NovyxRAMClient,
    MemoryItem,
)

# LangChain imports
try:
    from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
except ImportError:
    from langchain.schema import BaseMessage, HumanMessage, AIMessage

logger = logging.getLogger(__name__)

T = TypeVar('T')


# =============================================================================
# Integrity Client
# =============================================================================

class IntegrityClient:
    """
    Client for Novyx Integrity API.

    Handles challenge-response verification for secure memory writes.
    """

    DEFAULT_BASE_URL = "https://api.novyx.io/integrity"

    def __init__(
        self,
        api_key: str,
        shared_secret: str,
        base_url: Optional[str] = None,
        timeout: int = 30,
    ):
        """
        Initialize Integrity client.

        Args:
            api_key: Novyx Integrity API key (int_xxx)
            shared_secret: Shared secret for challenge-response
            base_url: Optional custom API URL
            timeout: Request timeout in seconds
        """
        self.api_key = api_key
        self.shared_secret = shared_secret
        self.base_url = (base_url or self.DEFAULT_BASE_URL).rstrip("/")
        self.timeout = timeout

        self._session = requests.Session()
        self._session.headers.update({
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "novyx-langchain/0.1.0",
        })

    def _solve_challenge(self, challenge_data: str, nonce: str) -> str:
        """Solve a cryptographic challenge."""
        message = (challenge_data + nonce).encode()
        return hmac.new(
            self.shared_secret.encode(),
            message,
            hashlib.sha256
        ).hexdigest()

    def _compute_hash(self, content: Any) -> str:
        """Compute SHA-256 hash of content."""
        if isinstance(content, str):
            data = content.encode()
        elif isinstance(content, bytes):
            data = content
        else:
            data = json.dumps(content, sort_keys=True, separators=(',', ':')).encode()
        return f"sha256:{hashlib.sha256(data).hexdigest()}"

    def verify_write(
        self,
        agent_id: str,
        artifact_id: str,
        content: Any,
        metadata: Optional[Dict] = None,
    ) -> bool:
        """
        Verify a write operation through challenge-response.

        Args:
            agent_id: Agent identifier
            artifact_id: Artifact/memory identifier
            content: Content being written
            metadata: Optional metadata

        Returns:
            True if verification successful

        Raises:
            IntegrityError: If verification fails
        """
        content_hash = self._compute_hash(content)

        # Step 1: Request challenge
        try:
            response = self._session.post(
                f"{self.base_url}/v1/verify/request",
                json={
                    "agent_id": agent_id,
                    "artifact_id": artifact_id,
                    "content_hash": content_hash,
                },
                timeout=self.timeout,
            )

            if response.status_code == 401:
                raise IntegrityError("Invalid Integrity API key")
            elif response.status_code == 429:
                raise IntegrityError("Rate limit exceeded")

            response.raise_for_status()
            challenge = response.json()

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to request verification: {e}")
            raise IntegrityError(f"Verification request failed: {e}")

        # Check if pre-verified
        if challenge.get("algorithm") == "pre_verified":
            return True

        # Step 2: Solve challenge
        solution = self._solve_challenge(
            challenge.get("challenge_data", ""),
            challenge.get("nonce", ""),
        )

        # Step 3: Confirm write
        try:
            response = self._session.post(
                f"{self.base_url}/v1/verify/confirm",
                json={
                    "challenge_id": challenge.get("challenge_id"),
                    "response": solution,
                    "content_hash": content_hash,
                    "metadata": metadata or {},
                },
                timeout=self.timeout,
            )

            response.raise_for_status()
            result = response.json()

            if not result.get("granted"):
                raise IntegrityError(
                    f"Write verification denied: {result.get('message', 'Unknown')}"
                )

            return True

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to confirm verification: {e}")
            raise IntegrityError(f"Verification confirmation failed: {e}")

    def get_status(self) -> Dict:
        """Get integrity status."""
        try:
            response = self._session.get(
                f"{self.base_url}/v1/integrity/status",
                timeout=self.timeout,
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get integrity status: {e}")
            return {"is_healthy": False, "error": str(e)}

    def is_healthy(self) -> bool:
        """Quick health check."""
        status = self.get_status()
        return status.get("is_healthy", False)


class IntegrityError(Exception):
    """Raised when integrity verification fails."""
    pass


# =============================================================================
# Protected Decorator
# =============================================================================

def protect(
    client: IntegrityClient,
    agent_id: Optional[str] = None,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator to protect memory operations with integrity verification.

    Usage:
        client = IntegrityClient(api_key="int_xxx", shared_secret="yyy")

        @protect(client, agent_id="my-agent")
        def store_memory(key: str, value: dict) -> str:
            # Your storage logic
            return memory_id

    Args:
        client: IntegrityClient instance
        agent_id: Optional agent identifier

    Returns:
        Decorated function with integrity verification
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs):
            aid = agent_id or func.__name__

            # Extract artifact_id and content from arguments
            artifact_id = kwargs.get('artifact_id') or kwargs.get('key')
            if not artifact_id and args:
                artifact_id = str(args[0])

            content = kwargs.get('content') or kwargs.get('value') or kwargs.get('observation')
            if not content and len(args) > 1:
                content = args[1]

            # Verify before executing
            if artifact_id and content:
                try:
                    client.verify_write(aid, str(artifact_id), content)
                except IntegrityError as e:
                    logger.error(f"Integrity verification failed: {e}")
                    raise

            return func(*args, **kwargs)

        return wrapper
    return decorator


# =============================================================================
# Integrity-Protected RAM Client
# =============================================================================

class IntegrityRAMClient(NovyxRAMClient):
    """
    Novyx RAM client with integrity verification on all writes.

    Every store/delete operation goes through cryptographic verification
    before being persisted.
    """

    def __init__(
        self,
        api_key: str,
        integrity_api_key: str,
        integrity_secret: str,
        base_url: Optional[str] = None,
        integrity_base_url: Optional[str] = None,
        agent_id: str = "langchain",
    ):
        """
        Initialize integrity-protected RAM client.

        Args:
            api_key: Novyx RAM API key
            integrity_api_key: Novyx Integrity API key
            integrity_secret: Shared secret for challenges
            base_url: Optional custom RAM API URL
            integrity_base_url: Optional custom Integrity API URL
            agent_id: Agent identifier for verification
        """
        super().__init__(api_key=api_key, base_url=base_url)

        self.integrity = IntegrityClient(
            api_key=integrity_api_key,
            shared_secret=integrity_secret,
            base_url=integrity_base_url,
        )
        self.agent_id = agent_id

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
        Store a memory with integrity verification.

        The write is cryptographically verified before persisting.
        """
        # Generate artifact ID
        artifact_id = hashlib.sha256(
            f"{observation}{time.time()}".encode()
        ).hexdigest()[:16]

        # Prepare content for verification
        content = {
            "observation": observation,
            "tags": tags or [],
            "importance": importance,
            "confidence": confidence,
        }

        # Verify the write
        self.integrity.verify_write(
            agent_id=agent_id or self.agent_id,
            artifact_id=artifact_id,
            content=content,
            metadata={
                "operation": "store",
                "source": "novyx-langchain",
                **(metadata or {}),
            },
        )

        # Proceed with storage
        return super().store(
            observation=observation,
            tags=tags,
            importance=importance,
            confidence=confidence,
            context_ids=context_ids,
            agent_id=agent_id or self.agent_id,
            metadata=metadata,
        )

    def delete_memory(self, memory_id: str) -> bool:
        """Delete a memory with integrity verification."""
        # Verify the delete
        self.integrity.verify_write(
            agent_id=self.agent_id,
            artifact_id=memory_id,
            content={"operation": "delete", "memory_id": memory_id},
            metadata={"operation": "delete"},
        )

        return super().delete_memory(memory_id)

    def clear_all(self, tags: Optional[List[str]] = None) -> int:
        """Clear all memories with integrity verification."""
        # Verify the clear operation
        self.integrity.verify_write(
            agent_id=self.agent_id,
            artifact_id="clear_all",
            content={"operation": "clear", "tags": tags or []},
            metadata={"operation": "clear_all"},
        )

        return super().clear_all(tags=tags)


# =============================================================================
# Integrity-Protected Chat Message History
# =============================================================================

class IntegrityChatMessageHistory(NovyxChatMessageHistory):
    """
    Chat message history with integrity verification.

    Every message is cryptographically verified before storage.
    """

    def __init__(
        self,
        api_key: str,
        integrity_api_key: str,
        integrity_secret: str,
        session_id: str,
        base_url: Optional[str] = None,
        integrity_base_url: Optional[str] = None,
        agent_id: Optional[str] = None,
        max_messages: int = 100,
    ):
        """Initialize integrity-protected chat history."""
        # Use integrity-protected client
        self.client = IntegrityRAMClient(
            api_key=api_key,
            integrity_api_key=integrity_api_key,
            integrity_secret=integrity_secret,
            base_url=base_url,
            integrity_base_url=integrity_base_url,
            agent_id=agent_id or "langchain",
        )

        self.session_id = session_id
        self.agent_id = agent_id or "langchain"
        self.max_messages = max_messages

        self._session_tag = f"session:{session_id}"
        self._message_tag = "chat:message"


# =============================================================================
# Integrity-Protected Memory Class
# =============================================================================

class NovyxIntegrityMemory(NovyxMemory):
    """
    Full-featured memory with integrity verification.

    This is the ONLY LangChain memory provider with tamper-proof writes.
    Every memory operation goes through cryptographic challenge-response
    authentication.

    Example:
        from novyx_langchain import NovyxIntegrityMemory
        from langchain.chains import ConversationChain

        memory = NovyxIntegrityMemory(
            api_key="nram_tenant_xxx",
            integrity_api_key="int_xxx",
            integrity_secret="your_shared_secret",
            session_id="user-123"
        )

        chain = ConversationChain(llm=llm, memory=memory)

        # All writes are now cryptographically verified!
        response = chain.invoke({"input": "Remember my name is Alice"})

    Security Features:
        - Challenge-response authentication on every write
        - SHA-256 content hashing
        - Immutable audit trail
        - Tamper detection
        - Forensic rollback capability
    """

    # Additional fields for integrity
    integrity_api_key: str = Field(..., description="Novyx Integrity API key")
    integrity_secret: str = Field(..., description="Shared secret for challenges")
    integrity_base_url: Optional[str] = Field(None, description="Integrity API URL")
    verify_on_read: bool = Field(False, description="Verify integrity on reads")

    _integrity_client: Optional[IntegrityClient] = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Override client with integrity-protected version
        self._client = IntegrityRAMClient(
            api_key=self.api_key,
            integrity_api_key=self.integrity_api_key,
            integrity_secret=self.integrity_secret,
            base_url=self.base_url,
            integrity_base_url=self.integrity_base_url,
            agent_id=self.agent_id,
        )

        # Override chat history with integrity-protected version
        self._chat_history = IntegrityChatMessageHistory(
            api_key=self.api_key,
            integrity_api_key=self.integrity_api_key,
            integrity_secret=self.integrity_secret,
            session_id=self.session_id,
            base_url=self.base_url,
            integrity_base_url=self.integrity_base_url,
            agent_id=self.agent_id,
        )

        # Initialize integrity client for status checks
        self._integrity_client = IntegrityClient(
            api_key=self.integrity_api_key,
            shared_secret=self.integrity_secret,
            base_url=self.integrity_base_url,
        )

    def get_integrity_status(self) -> Dict:
        """
        Get current integrity status.

        Returns:
            Dict with integrity score, health status, and alerts
        """
        return self._integrity_client.get_status()

    def is_integrity_healthy(self) -> bool:
        """Check if integrity system is healthy."""
        return self._integrity_client.is_healthy()

    def load_memory_variables(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Load memory with optional integrity verification."""
        result = super().load_memory_variables(inputs)

        if self.verify_on_read:
            # Verify integrity status before returning
            status = self.get_integrity_status()
            if not status.get("is_healthy", False):
                logger.warning(
                    f"Integrity warning: {status.get('issues', ['Unknown'])}"
                )

        return result


# =============================================================================
# Factory Functions
# =============================================================================

def create_integrity_memory(
    ram_api_key: str,
    integrity_api_key: str,
    integrity_secret: str,
    session_id: str,
    **kwargs,
) -> NovyxIntegrityMemory:
    """
    Factory function to create integrity-protected memory.

    Args:
        ram_api_key: Novyx RAM API key
        integrity_api_key: Novyx Integrity API key
        integrity_secret: Shared secret for verification
        session_id: Session identifier
        **kwargs: Additional arguments for NovyxIntegrityMemory

    Returns:
        Configured NovyxIntegrityMemory instance

    Example:
        memory = create_integrity_memory(
            ram_api_key="nram_xxx",
            integrity_api_key="int_xxx",
            integrity_secret="secret",
            session_id="user-123",
            k=10,
            return_messages=True
        )
    """
    return NovyxIntegrityMemory(
        api_key=ram_api_key,
        integrity_api_key=integrity_api_key,
        integrity_secret=integrity_secret,
        session_id=session_id,
        **kwargs,
    )
