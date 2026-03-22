# Codebase Guide

Codebase indexing and semantic search that enables AI to understand your project structure.

## Overview

Codebase module provides:
- **Project Indexing** - Scan and index project files
- **Semantic Search** - Search code using natural language
- **Context Generation** - Generate complete context for development tasks

## Quick Start

```python
from h_agent.codebase import CodebaseIndex, CodeSearch, ContextGenerator

# 1. Index project
index = CodebaseIndex("/path/to/project")
info = index.scan()
print(f"Indexed {info['file_count']} files, {info['chunk_count']} code chunks")

# 2. Search code
search = CodeSearch()
results = search.search("User authentication logic")

# 3. Generate development context
generator = ContextGenerator()
ctx = generator.generate_context(
    project_path="/path/to/project",
    task="Add user comment feature"
)
print(ctx.to_markdown())
```

## Project Indexing

### Basic Usage

```python
from h_agent.codebase import CodebaseIndex

# Create index
index = CodebaseIndex("/path/to/project")

# Full scan
info = index.scan(incremental=False)

# Incremental update (only reindex modified files)
info = index.scan(incremental=True)

# Get project info
info = index.get_info()
print(info)
# {
#     'project_name': 'myapp',
#     'file_count': 150,
#     'chunk_count': 892,
#     'languages': {'python': 450, 'javascript': 442},
#     'scan_time': 1699999999.0
# }
```

### Supported Languages

Automatically recognize and extract code blocks:

| Language | Supported Block Types |
|------|-------------|
| Python | class, function, method |
| JavaScript/TypeScript | function, class |
| Go | function |
| Rust | function, struct |
| Java | class, method |
| Ruby | method, class |
| Vue | script, template |

### Manual Scanning

```python
from h_agent.codebase.indexer import FileIndexer

# Only scan files without indexing
indexer = FileIndexer("/path/to/project")
files = indexer.scan_project()

# View directory tree
tree = indexer.get_directory_tree()

# Get modified files
import time
since = time.time() - 86400  # Past 24 hours
changed = indexer.get_changed_files(since)
```

## Semantic Search

### Basic Search

```python
from h_agent.codebase import CodeSearch

search = CodeSearch()

# Natural language query
results = search.search("Handle user login")

# Search results
for result in results:
    print(f"{result.name} ({result.similarity:.2%})")
    print(f"  {result.file_path}:{result.start_line}")
    print(f"  {result.source_code[:100]}...")
```

### Filtered Search

```python
# Filter by file type
results = search.search(
    "Database operations",
    chunk_types=["function", "method"],  # Only search functions/methods
)

# Filter by language
results = search.search(
    "API routes",
    languages=["python", "go"],  # Only search Python and Go
)

# Filter by similarity
results = search.search(
    "Authentication",
    min_similarity=0.5,  # At least 50% similarity
)
```

### Project-specific Search

```python
# Search only in specific project
results = search.search(
    "Cache implementation",
    project_path="/path/to/project",
    top_k=10,  # Return more results
)
```

### Find Similar Code

```python
# Find code similar to a certain code chunk
similar = search.find_similar_chunks(
    chunk_id="auth.user_login",
    project_path="/path/to/project",
)

# View all code chunks in a file
file_chunks = search.search_by_file(
    file_path="src/auth.py",
    project_path="/path/to/project",
)
```

## Context Generation

### Generate Task Context

```python
from h_agent.codebase import ContextGenerator

generator = ContextGenerator()

# Generate context for development task
ctx = generator.generate_context(
    project_path="/path/to/project",
    task="Add social sharing feature",
    top_k=5,  # Number of relevant code pieces
    min_similarity=0.3,  # Minimum similarity
)

# Output as Markdown
print(ctx.to_markdown())
```

### Output Format

Markdown output contains:

```
# Development Context: Add social sharing feature

**Project:** myapp
**Path:** /path/to/project

## Project Overview
- Files: 150
- Code chunks: 892
- Total lines: 45,230

### Languages
- python: 450 chunks
- javascript: 442 chunks

## Relevant Files
- `src/share.py` (python) - 1 class(es), including ShareService
- `src/models/post.py` (python) - 1 class(es), including Post

## Relevant Code

### 1. ShareService (class)
**File:** `src/share.py` (lines 15-80)
**Similarity:** 85.2%

```python
class ShareService:
    def __init__(self, db):
        self.db = db
    
    def share_to_social(self, platform, content):
        ...
```

## Cross-Project Patterns

### class: service
**Similarity:** 82.5%
**Files:** src/share.py, src/email.py, src/notification.py

Found 3 similar class(es) named 'service'
```

### Quick Context

```python
# One line to get context
generator = ContextGenerator()
markdown = generator.quick_context(
    project_path="/path/to/project",
    task="Add comment feature",
)
print(markdown)
```

## CLI Usage

```bash
# Index project
python -m h_agent.codebase /path/to/project scan

# Search code
python -m h_agent.codebase /path/to/project search "user authentication"

# Generate context
python -m h_agent.codebase /path/to/project context "Add sharing feature"
```

## Configuration

### Index Storage

Default storage at `~/.h-agent/codebase_index/`

```python
from h_agent.codebase import CodebaseIndex
from pathlib import Path

# Custom index directory
index = CodebaseIndex(
    "/path/to/project",
    index_dir=Path("/custom/path"),
)
```

### Embedding Model

```python
from h_agent.codebase import CodeSearch

# Use advanced embedding (requires sentence-transformers)
search = CodeSearch(
    embedder_model="all-MiniLM-L6-v2",  # Default
    use_advanced_embeddings=True,
)

# Or use simple TF-IDF embedding (no dependencies)
search = CodeSearch(
    use_advanced_embeddings=False,
)
```

Install sentence-transformers:
```bash
pip install sentence-transformers
```

## Best Practices

### 1. Regular Incremental Indexing

```python
# Incremental indexing in CI/CD
index = CodebaseIndex(project_path)
index.scan(incremental=True)  # Only update modified files
```

### 2. Limit Result Count

```python
# Avoid returning too many results
results = search.search(
    "Authentication",
    top_k=5,  # Limit count
    min_similarity=0.4,  # Raise threshold
)
```

### 3. Combine with Context

```python
# Search + context generation
search = CodeSearch()
ctx = generator.generate_context(
    project_path=project,
    task=task_description,
    top_k=3,  # Just a few relevant code pieces
)

# Pass context to AI
response = openai.chat.completions.create(
    messages=[
        {"role": "system", "content": "You are an assistant."},
        {"role": "user", "content": ctx.to_markdown()},
    ],
)
```
