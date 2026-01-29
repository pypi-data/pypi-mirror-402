"""
novyx-langchain: Persistent Memory for LangChain Agents
========================================================

Provides semantic memory storage and retrieval using Novyx RAM,
with optional tamper-proof verification via Novyx Integrity.

Basic Usage:
    from novyx_langchain import NovyxMemory

    memory = NovyxMemory(
        api_key="nram_tenant_xxx",
        session_id="user-123"
    )

    # Use with LangChain
    chain = ConversationChain(llm=llm, memory=memory)

LangGraph Usage:
    from novyx_langchain import NovyxCheckpointer

    checkpointer = NovyxCheckpointer(api_key="nram_tenant_xxx")
    graph = workflow.compile(checkpointer=checkpointer)

Integrity-Protected Usage:
    from novyx_langchain import NovyxIntegrityMemory

    memory = NovyxIntegrityMemory(
        api_key="nram_tenant_xxx",
        integrity_api_key="int_xxx",
        integrity_secret="yyy"
    )
"""

__version__ = "0.1.0"
__author__ = "Novyx Labs"

from novyx_langchain.memory import (
    NovyxMemory,
    NovyxChatMessageHistory,
    NovyxRAMClient,
)
from novyx_langchain.checkpointer import NovyxCheckpointer
from novyx_langchain.integrity import NovyxIntegrityMemory
from novyx_langchain.buffer import NovyxBufferedMemory

__all__ = [
    "NovyxMemory",
    "NovyxChatMessageHistory",
    "NovyxRAMClient",
    "NovyxCheckpointer",
    "NovyxIntegrityMemory",
    "NovyxBufferedMemory",
    "__version__",
]
