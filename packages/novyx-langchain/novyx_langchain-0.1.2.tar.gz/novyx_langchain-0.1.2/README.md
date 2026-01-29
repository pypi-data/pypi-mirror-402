# novyx-langchain

[![PyPI version](https://img.shields.io/pypi/v/novyx-langchain.svg)](https://pypi.org/project/novyx-langchain/)
[![Python versions](https://img.shields.io/pypi/pyversions/novyx-langchain.svg)](https://pypi.org/project/novyx-langchain/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Downloads](https://img.shields.io/pypi/dm/novyx-langchain.svg)](https://pypi.org/project/novyx-langchain/)

**Persistent semantic memory for LangChain agents.**

Your agents forget. Novyx remembers.

```python
from novyx_langchain import NovyxMemory
from langchain.chains import ConversationChain
from langchain_openai import ChatOpenAI

memory = NovyxMemory(api_key="nram_xxx", session_id="user-123")
chain = ConversationChain(llm=ChatOpenAI(), memory=memory)

response = chain.invoke({"input": "My name is Alice"})
# Memory persists across restarts, deployments, and servers
```

## Features

- **Semantic retrieval** - Finds relevant context, not just recent messages
- **LangGraph native** - First-class checkpointer support
- **Multi-tenant** - Built for production SaaS applications
- **Tamper-proof** - Optional integrity verification (unique to Novyx)
- **< 100ms latency** - Fast semantic search via Novyx RAM
- **CRDT conflict resolution** - Handles concurrent writes gracefully

## Installation

```bash
pip install novyx-langchain
```

For LangGraph support:
```bash
pip install "novyx-langchain[langgraph]"
```

## Quick Start

### 1. Get an API Key

Sign up at [novyxlabs.com](https://novyxlabs.com) to get your API key.

### 2. Basic Memory

```python
from novyx_langchain import NovyxMemory
from langchain.chains import ConversationChain
from langchain_openai import ChatOpenAI

# Create persistent memory
memory = NovyxMemory(
    api_key="nram_tenant_xxx",
    session_id="user-123",
    k=10,  # Retrieve top 10 relevant memories
)

# Use with any LangChain chain
chain = ConversationChain(
    llm=ChatOpenAI(model="gpt-4"),
    memory=memory,
)

# Conversations persist automatically
response = chain.invoke({"input": "Remember that I prefer dark mode"})
# ... restart your app ...
response = chain.invoke({"input": "What are my preferences?"})
# Agent remembers dark mode preference!
```

### 3. LangGraph Checkpointer

```python
from langgraph.graph import StateGraph, END
from novyx_langchain import NovyxCheckpointer

# Create checkpointer
checkpointer = NovyxCheckpointer(api_key="nram_tenant_xxx")

# Build your graph
builder = StateGraph(AgentState)
builder.add_node("agent", agent_node)
builder.add_node("tools", tool_node)
builder.set_entry_point("agent")
builder.add_edge("agent", END)

# Compile with persistence
graph = builder.compile(checkpointer=checkpointer)

# Run with thread_id
config = {"configurable": {"thread_id": "conv-123"}}
result = graph.invoke({"messages": [HumanMessage("Hello!")]}, config)

# State persists across invocations
```

### 4. Integrity-Protected Memory (Tamper-Proof)

```python
from novyx_langchain import NovyxIntegrityMemory

# Every write is cryptographically verified
memory = NovyxIntegrityMemory(
    api_key="nram_tenant_xxx",
    integrity_api_key="int_xxx",
    integrity_secret="your_shared_secret",
    session_id="user-123",
)

chain = ConversationChain(llm=llm, memory=memory)

# All writes verified with challenge-response authentication
# Tamper detection, audit trails, forensic rollback
response = chain.invoke({"input": "Store sensitive context"})
```

## API Reference

### NovyxMemory

Main memory class, compatible with `ConversationBufferMemory`.

```python
NovyxMemory(
    api_key: str,              # Novyx RAM API key
    session_id: str,           # Unique session identifier
    k: int = 10,               # Number of memories to retrieve
    semantic_search: bool = True,  # Use semantic (vs recency) retrieval
    return_messages: bool = False,  # Return Message objects vs string
    min_relevance: float = 0.3,    # Minimum relevance score
)
```

**Methods:**
- `load_memory_variables(inputs)` - Load relevant memories
- `save_context(inputs, outputs)` - Save conversation turn
- `clear()` - Clear session memory
- `search(query, limit)` - Semantic search
- `store_memory(content, tags, importance)` - Store custom memory

### NovyxChatMessageHistory

For use with `RunnableWithMessageHistory`:

```python
from langchain_core.runnables.history import RunnableWithMessageHistory
from novyx_langchain import NovyxChatMessageHistory

def get_session_history(session_id: str):
    return NovyxChatMessageHistory(
        api_key="nram_xxx",
        session_id=session_id,
    )

chain_with_history = RunnableWithMessageHistory(
    chain,
    get_session_history,
)
```

### NovyxCheckpointer

LangGraph checkpoint persistence:

```python
NovyxCheckpointer(
    api_key: str,              # Novyx RAM API key
    namespace: str = "langgraph",  # Namespace for isolation
)
```

**Methods:**
- `put(config, checkpoint, metadata)` - Store checkpoint
- `get_tuple(config)` - Get checkpoint
- `list(config)` - List checkpoints
- `clear_thread(thread_id)` - Clear thread checkpoints

### NovyxIntegrityMemory

Tamper-proof memory with cryptographic verification:

```python
NovyxIntegrityMemory(
    api_key: str,              # Novyx RAM API key
    integrity_api_key: str,    # Novyx Integrity API key
    integrity_secret: str,     # Shared secret for challenges
    session_id: str,
    # ... same options as NovyxMemory
)
```

### NovyxBufferedMemory

High-throughput memory with local buffering:

```python
NovyxBufferedMemory(
    api_key: str,
    session_id: str,
    buffer_size: int = 50,     # Flush after N messages
    flush_interval: float = 30.0,  # Or flush every N seconds
)
```

## Examples

### Multi-Tenant Setup

```python
def get_memory_for_user(user_id: str) -> NovyxMemory:
    return NovyxMemory(
        api_key=f"nram_{tenant_id}_xxx",  # Tenant-specific key
        session_id=f"user-{user_id}",
        k=20,
    )

# Each user has isolated memory
alice_memory = get_memory_for_user("alice")
bob_memory = get_memory_for_user("bob")
```

### Custom Tags and Importance

```python
memory = NovyxMemory(api_key="nram_xxx", session_id="user-123")

# Store with custom tags and importance
memory.store_memory(
    content="User is a premium subscriber",
    tags=["subscription", "important"],
    importance=9,  # High importance (1-10)
)

# Search by tags
results = memory.search("subscription status", limit=5)
```

### AgentExecutor Integration

```python
from langchain.agents import AgentExecutor, create_openai_functions_agent

memory = NovyxMemory(
    api_key="nram_xxx",
    session_id="agent-session",
    return_messages=True,
)

agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    memory=memory,
    verbose=True,
)

result = agent_executor.invoke({"input": "What do you remember about me?"})
```

## Environment Variables

```bash
export NOVYX_RAM_API_KEY="nram_tenant_xxx"
export NOVYX_RAM_URL="https://novyx-ram-api.fly.dev/v1"  # Optional
export NOVYX_INTEGRITY_API_KEY="int_xxx"  # For integrity features
export NOVYX_INTEGRITY_SECRET="your_secret"
```

## Comparison

| Feature | novyx-langchain | ConversationBufferMemory | Zep | Mem0 |
|---------|-----------------|-------------------------|-----|------|
| Semantic search | ✅ | ❌ | ✅ | ✅ |
| Tamper-proof | ✅ | ❌ | ❌ | ❌ |
| LangGraph native | ✅ | ❌ | ❌ | ❌ |
| Multi-tenant | ✅ | ❌ | ✅ | ✅ |
| Self-hostable | ✅ | N/A | ✅ | ✅ |
| Conflict resolution | ✅ CRDT | ❌ | ❌ | ❌ |
| < 100ms latency | ✅ | ✅ | ✅ | ✅ |

## License

MIT License - see [LICENSE](LICENSE) for details.

## Links

- [Documentation](https://docs.novyxlabs.com/integrations/langchain)
- [GitHub](https://github.com/novyxlabs/novyx-langchain)
- [Novyx RAM API](https://novyxlabs.com/ram)
- [Novyx Integrity](https://novyxlabs.com/integrity)
- [Discord](https://discord.gg/novyx)
