# Memory Guide

h-agent's memory system supporting short-term, long-term, and contextual memory.

## Overview

Memory system is divided into three layers:
1. **Context Memory** - Current session's context
2. **Short-term Memory** - Recent interaction summaries
3. **Long-term Memory** - Cross-session persistent knowledge

## Quick Start

```python
from h_agent.memory import Memory, LongTermMemory

# Create memory instance
memory = Memory()

# Add memory
memory.add("User asked about Python async programming", importance=8)

# Get relevant memory
context = memory.get_relevant("async programming")
print(context)

# Save session
memory.save_session("session-123", summary="Discussed async programming")
```

## Context Memory

### Managing Context

```python
from h_agent.memory.context import ContextManager

ctx = ContextManager(
    max_tokens=100000,  # Max tokens
    reserved_tokens=5000,  # Reserved space
)

# Add context
ctx.add("System: You are an assistant", role="system")
ctx.add("User: Help me write a function", role="user")
ctx.add("Assistant: Of course...", role="assistant")

# Get complete context
messages = ctx.get_messages()

# Get compressed context (when exceeding limit)
compressed = ctx.get_compressed()

# Estimate current token count
tokens = ctx.estimate_tokens()
```

### Context Window

```python
# Set context window
ctx.set_window(
    system="You are a Python assistant",
    max_history=10,  # Last 10 conversation turns
)

# Add conversation
ctx.add_message("User", "What are decorators?")
ctx.add_message("Assistant", "Decorators are...")
ctx.add_message("User", "Give an example")

# Get window content
messages = ctx.get_window()
```

## Short-term Memory

### Memory Manager

```python
from h_agent.memory import Memory

memory = Memory(
    max_items=100,  # Max memory entries
    importance_threshold=5,  # Importance threshold
)

# Add memory
memory.add(
    "User likes using Python",
    importance=7,
    tags=["python", "preference"],
)

memory.add(
    "Project uses FastAPI framework",
    importance=9,
    tags=["project", "fastapi"],
)

# Get recent memories
recent = memory.get_recent(limit=10)

# Search relevant memories
relevant = memory.get_relevant("Python async")

# Summarize memories
summary = memory.summarize()
```

### Memory Structure

```python
# Memory entry
memory.add(
    content="User's work email is user@company.com",
    importance=8,
    category="user_info",
    tags=["email", "work"],
    metadata={"source": "conversation"},
)

# Get categorized memories
email_memories = memory.get_by_category("user_info")

# Get memories with tags
python_memories = memory.get_by_tags(["python"])
```

## Long-term Memory

### Persistent Storage

```python
from h_agent.memory.long_term import LongTermMemory

# Create long-term memory storage
ltm = LongTermMemory(
    db_path="~/.h-agent/memory/long_term.db",
)

# Add memory
ltm.add(
    content="User prefers dark theme",
    memory_type="preference",
    importance=7,
)

# Search memories
results = ltm.search("theme color")
for result in results:
    print(f"{result['content']} (relevance: {result['score']})")

# Get memory
memory = ltm.get(memory_id)

# Update memory
ltm.update(memory_id, content="New content")

# Delete memory
ltm.delete(memory_id)
```

### Memory Retrieval

```python
# Semantic search
results = ltm.search(
    "Which city is the user in",
    limit=5,
    memory_types=["personal"],
)

# Time range search
from datetime import datetime, timedelta
recent = ltm.search_by_time(
    start=datetime.now() - timedelta(days=7),
    end=datetime.now(),
)

# Statistics
stats = ltm.get_stats()
print(f"Total memories: {stats['total']}")
print(f"By type: {stats['by_type']}")
```

## Memory Summarization

### Automatic Summarization

```python
from h_agent.memory.summarizer import Summarizer

summarizer = Summarizer(
    model="gpt-4o-mini",
    api_key="sk-...",
)

# Summarize conversation
summary = await summarizer.summarize_conversation(messages)

# Incremental summarization (for long conversations)
previous_summary = "User asked some Python questions"
new_summary = await summarizer.summarize_incremental(
    previous_summary,
    new_messages,
)

# Extract key information
entities = await summarizer.extract_entities(messages)
# {'people': ['John'], 'organizations': [], 'topics': ['Python']}
```

### Memory Compression

```python
# Compress low-importance memories
memory.compact(
    keep_high_importance=True,
    target_size=50,
)

# Compress by time
memory.compact_by_time(
    older_than=datetime.now() - timedelta(days=30),
)
```

## Session Management

### Save and Load Sessions

```python
# Save session
from h_agent.memory import SessionManager

sm = SessionManager()

session_id = sm.save_session(
    messages=[
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi!"},
    ],
    metadata={
        "user_id": "user-123",
        "topic": "general",
    },
)

# Load session
session = sm.load_session(session_id)
messages = session["messages"]

# List sessions
sessions = sm.list_sessions(
    limit=10,
    filter_by={"user_id": "user-123"},
)
```

### Session Summarization

```python
# Auto-generate summary
summary = sm.generate_summary(session_id)

# Update summary
sm.update_summary(session_id, "User asked about API usage")

# Search sessions
found = sm.search_sessions("API usage")
```

## Retrieval Augmentation

### RAG Retrieval

```python
from h_agent.features.rag import MemoryRetriever

retriever = MemoryRetriever(
    memory_backend="chroma",  # or "sqlite"
    embedding_model="all-MiniLM-L6-v2",
)

# Add to retrieval index
retriever.add_memory(
    content="User uses FastAPI framework",
    metadata={"source": "conversation"},
)

# Retrieve
results = retriever.retrieve(
    query="What framework does the user use?",
    limit=3,
)

# Get context for agent
context = retriever.get_context_for_agent(query)
```

## Best Practices

### 1. Importance Scoring

```python
# High importance (>7): Key decisions, user preferences, task goals
memory.add("User wants project completed by end of month", importance=9)

# Medium importance (4-6): General information, temporary state
memory.add("Currently discussing authentication module", importance=5)

# Low importance (<4): Casual conversation, daily interactions
memory.add("User said thank you", importance=2)
```

### 2. Using Tags

```python
# Organize memories with tags
memory.add("User is in China", tags=["location", "personal"])

# Batch retrieval
relevant = memory.get_by_tags(["location", "work"])
```

### 3. Regular Cleanup

```python
# Clean up low-value memories
memory.cleanup(min_importance=3)

# Merge similar memories
memory.merge_similar(threshold=0.8)
```

### 4. Session Isolation

```python
# Different users/projects use different sessions
session_manager = SessionManager()

# Project A session
session_a = session_manager.create_session(project="project-a")

# Project B session
session_b = session_manager.create_session(project="project-b")
```

## Configuration

### Storage Configuration

```python
from h_agent.memory import MemoryConfig

config = MemoryConfig(
    # Storage path
    storage_dir="~/.h-agent/memory",
    
    # Short-term memory
    short_term_max=100,
    short_term_importance_threshold=5,
    
    # Long-term memory
    long_term_enabled=True,
    long_term_db="sqlite",
    
    # RAG
    rag_enabled=True,
    embedding_model="all-MiniLM-L6-v2",
)

memory = Memory(config=config)
```

### Environment Variables

```bash
# Memory storage
export MEMORY_STORAGE_DIR=~/.h-agent/memory

# RAG configuration
export RAG_EMBEDDING_MODEL=all-MiniLM-L6-v2
export RAG_VECTOR_DB=chroma
```
