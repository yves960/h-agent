## Product Design

### Command List

#### Core Service Commands
- `h-agent start` - Start background service
  - `--port PORT` - Specify service port (default: 8080)
  - `--host HOST` - Specify bind address (default: 127.0.0.1)
  - `--daemon` - Run as daemon (optional)
- `h-agent status` - Check service status
  - Shows whether running, PID, port, uptime, etc.
- `h-agent stop` - Stop background service
  - Safely close all sessions and save state

#### Session Management Commands
- `h-agent session list` - List all sessions
  - `--agent AGENT_ID` - Specify agent (default: default)
  - `--limit N` - Limit number of results (default: 10)
- `h-agent session create --name "project-x"` - Create new session
  - `--agent AGENT_ID` - Specify agent (default: default)
  - Returns the created session ID
- `h-agent session history project-x` - View session history
  - `--limit N` - Limit message count (default: 50)
  - `--format FORMAT` - Output format (jsonl, json, text)
- `h-agent session delete project-x` - Delete specified session
  - `--force` - Force delete (no confirmation)

#### Chat Commands
- `h-agent chat --session project-x "help me analyze this code"` - Chat in specified session
  - `--stream` - Stream output response
  - `--timeout SECONDS` - Set timeout
- `h-agent run --session project-x "continue completing the task"` - Send single message to specified session
  - Non-interactive, suitable for script invocation
  - `--output FILE` - Save response to file

#### Configuration Commands (extensions to existing)
- `h-agent config --show` - Show configuration
- `h-agent config --api-key KEY` - Set API key
- `h-agent config --base-url URL` - Set API base URL
- `h-agent config --model MODEL` - Set model

### Architecture Design

#### Backend Service Architecture

**Layered Architecture:**

1. **CLI Layer** (`h_agent.cli.commands`)
   - Parse command line arguments
   - Route to corresponding server endpoints or local operations
   - Support two modes:
     - **Local mode**: Directly call core functions (when no backend service)
     - **Client mode**: Call backend service via HTTP API

2. **HTTP API Layer** (`h_agent.api.server`)
   - FastAPI/Flask server
   - RESTful API endpoints
   - WebSocket support for streaming responses
   - Process management (start/stop/status)

3. **Core Service Layer** (`h_agent.core.service`)
   - Agent instance management
   - Session lifecycle management
   - Request queue and concurrency control
   - Resource cleanup and monitoring

4. **Persistence Layer** (`h_agent.features.sessions`)
   - Extended from existing SessionStore
   - Support multiple agents and multiple sessions
   - JSONL file storage format remains unchanged

**Process Model:**
- Main process: HTTP server + Agent manager
- Worker process: Each active session may have its own context
- Daemon: Periodically clean up expired resources

**Communication Protocol:**
- HTTP/REST for commands
- WebSocket for streaming responses
- Unix socket as alternative for local communication

**Key Components:**

```python
# h_agent.api.server
class AgentAPIServer:
    def __init__(self):
        self.agent_manager = AgentManager()
        self.session_store = SessionStore()
    
    def start(self, host="127.0.0.1", port=8080):
        # Start HTTP server
    
    def stop(self):
        # Stop server and save state

# h_agent.core.service
class AgentManager:
    def __init__(self):
        self.agents = {}  # agent_id -> AgentInstance
    
    def get_or_create_agent(self, agent_id: str) -> AgentInstance:
        if agent_id not in self.agents:
            self.agents[agent_id] = AgentInstance(agent_id)
        return self.agents[agent_id]
    
    def cleanup_inactive_agents(self):
        # Clean up long-inactive agents

class AgentInstance:
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.session_store = SessionStore(agent_id)
        self.context_guard = ContextGuard()
```

### Data Storage

#### Session Persistence Scheme

**Storage Location:**
- Default: `~/.h-agent/sessions/` (global) or `.agent_workspace/sessions/` under project directory
- Configurable: Via environment variable or config file

**File Structure:**
```
sessions/
├── default/
│   ├── index.json          # Session index
│   ├── sess-abc123.jsonl   # Session data
│   └── sess-def456.jsonl
├── project-x/
│   ├── index.json
│   └── sess-xyz789.jsonl
└── ...
```

**SessionStore Enhancements:**
1. **Thread Safety**: Add file lock mechanism to prevent concurrent write conflicts
2. **Auto Cleanup**: Support TTL (Time To Live) for automatic deletion of expired sessions
3. **Compression Optimization**: Auto-compress large files (gzip) to save space
4. **Backup Mechanism**: Auto-backup important sessions

**Data Format:**
- **index.json**: Session metadata index
  ```json
  {
    "sess-abc123": {
      "session_id": "sess-abc123",
      "agent_id": "default",
      "created_at": "2026-03-20T14:00:00",
      "updated_at": "2026-03-20T14:30:00",
      "message_count": 25,
      "token_count": 15000,
      "name": "project-x"
    }
  }
  ```
- **sess-*.jsonl**: One message object per line, maintaining existing format compatibility

**Performance Optimization:**
- Memory cache: Active session message history cached in memory
- Lazy loading: Inactive sessions loaded from disk on demand
- Batch writing: Reduce frequent small file writes

### Task Breakdown

#### Tasks Assignable to Eck

**Phase 1: Core Infrastructure (High Priority)**
1. **Implement HTTP API Server**
   - Create `h_agent/api/server.py`
   - Implement basic start/stop/status endpoints
   - Integrate existing SessionStore
   
2. **Extend CLI Command Parsing**
   - Modify `h_agent/cli/commands.py`
   - Add new subcommands: start, stop, status, session, chat, run
   - Implement client mode (detect if backend service exists)

3. **Agent Manager Core**
   - Create `h_agent/core/service.py`
   - Implement AgentManager and AgentInstance classes
   - Support multi-agent isolation

**Phase 2: Session Feature Enhancement (Medium Priority)**
4. **SessionStore Thread Safety Refactor**
   - Add file lock mechanism
   - Implement concurrent-safe read/write operations
   
5. **Session Naming and Management**
   - Extend SessionStore to support custom session names
   - Implement session create/delete/list/history commands

6. **Data Persistence Optimization**
   - Add auto cleanup and TTL support
   - Implement compression and backup mechanisms

**Phase 3: Advanced Features (Low Priority)**
7. **WebSocket Streaming Response**
   - Implement streaming chat API
   - CLI supports --stream parameter
   
8. **Configuration Management Extension**
   - Support service-level configuration (port, host, etc.)
   - Implement config hot reload

9. **Monitoring and Logging**
   - Add detailed logging
   - Implement basic monitoring metrics

**Tech Stack Recommendations:**
- Web framework: FastAPI (good async support, comprehensive type hints)
- Process management: Use standard library multiprocessing or third-party like uvicorn
- File locking: fcntl (Unix) or portalocker (cross-platform)
- Configuration: Continue using existing config system, extend to support service config

**Acceptance Criteria:**
- All intended usage commands work correctly
- Backend service runs stably with reasonable resource usage
- Session data persistence is reliable with no data loss
- Backward compatible with existing interaction modes
