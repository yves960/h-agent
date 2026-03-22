# Agent Adapter & Web Capability Design

## 1. CLI Agent Research Report

### 1.1 opencode
- **Invocation**: `opencode run <message>` (non-interactive), `opencode serve` (HTTP service), `opencode acp` (ACP protocol)
- **Communication Protocol**: 
  - `run`: stdout outputs text, structured data via ANSI color encoding
  - `serve`: HTTP SSE streaming output
  - `acp`: Agent Client Protocol (JSON-RPC over HTTP)
- **Process Management**: subprocess.Popen, supports `--print-logs --log-level`
- **Output Format**: Terminal-friendly colored output, can be redirected via `--print-logs`
- **Status**: Common internal tool, pre-configured with multiple agents (sisyphus, hephaestus, oracle, etc.)

### 1.2 claude (Anthropic)
- **Invocation**: `claude --print <prompt>` (non-interactive)
- **Communication Protocol**: CLI outputs JSON/text to stdout
- **Process Management**: subprocess.run, supports `--output-format=stream-json`
- **Output Format**: Supports streaming JSON (`--include-partial-messages --output-format=stream-json`)
- **Status**: Installed

### 1.3 aider
- **Invocation**: `aider --no-autocomplete --no-git --read <file> --message "<prompt>"`
- **Communication Protocol**: CLI output
- **Status**: Not installed (requires `pip install aider`)

### 1.4 Unified Interface Design

```python
class BaseAgentAdapter(ABC):
    @abstractmethod
    def chat(self, message: str, **kwargs) -> AgentResponse: ...
    
    @abstractmethod
    def stream_chat(self, message: str, **kwargs) -> Iterator[str]: ...
    
    @abstractmethod
    def stop(self): ...
    
    @property
    @abstractmethod
    def name(self) -> str: ...

@dataclass
class AgentResponse:
    content: str
    tool_calls: list[ToolCall] | None
    error: str | None
    metadata: dict
```

## 2. Playwright Web Module

### 2.1 Feature List
- `playwright_launch()` - Launch browser
- `playwright_navigate(url)` - Navigate to URL
- `playwright_click(selector)` - Click element
- `playwright_type(selector, text)` - Type text
- `playwright_screenshot()` - Take screenshot
- `playwright_get_headers()` - Get page request/response headers
- `playwright_extract_tokens()` - Extract tokens from localStorage/sessionStorage
- `playwright_evaluate(script)` - Execute JS

### 2.2 Token-Free Login Mechanism
- Save cookies/localStorage of logged-in websites
- Restore session state on next launch
- Support import/export of session state

### 2.3 MCP Protocol Integration
- Exposed as MCP tools via `playwright_mcp_server`
- Tool list: `playwright_navigate`, `playwright_click`, `playwright_type`, `playwright_screenshot`, `playwright_evaluate`, `playwright_get_cookies`, `playwright_set_cookies`
