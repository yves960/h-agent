# Installation and Deployment

*"If there are limits, why haven't I found them?"* — Ekko

This document covers the complete installation process for h-agent, including Windows, Linux/macOS, intranet environments, and offline deployment.

---

## 1. Prerequisites

### System Requirements

| Requirement | Description |
|------|------|
| Python | 3.10+ |
| pip | Latest version (`pip install --upgrade pip`) |
| Disk Space | ~100 MB (with dependencies) |
| Network | Need access to OpenAI API (domestic users need proxy or use domestic models) |

### API Key Preparation

h-agent supports all OpenAI-compatible APIs. Common configurations:

| Provider | Base URL | Model Examples |
|--------|----------|----------|
| OpenAI | `https://api.openai.com/v1` | `gpt-4o`, `gpt-4o-mini` |
| DeepSeek | `https://api.deepseek.com/v1` | `deepseek-chat` |
| Zhipu AI | `https://open.bigmodel.cn/api/paas/v4` | `glm-4` |
| Azure OpenAI | `https://<resource>.openai.azure.com/v1` | `gpt-4o` |
| Local Ollama | `http://localhost:11434/v1` | `llama3`, `qwen2` |

---

## 2. Standard Installation

### pip Installation (Recommended)

```bash
pip install h-agent
```

### Source Installation (Development Version)

```bash
git clone https://github.com/ekko-ai/h-agent.git
cd h-agent
pip install -e .
```

### Installation with Optional Dependencies

```bash
# RAG support
pip install h-agent[rag]

# Development dependencies
pip install h-agent[dev]

# All dependencies
pip install h-agent[all]
```

---

## 3. Windows Installation

### PowerShell (Recommended)

```powershell
# 1. Clone project
git clone https://github.com/ekko-ai/h-agent.git
cd h-agent

# 2. Create virtual environment (recommended)
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 3. Install
pip install -e .

# 4. Initialize configuration
h-agent init
```

### CMD

```cmd
git clone https://github.com/ekko-ai/h-agent.git
cd h-agent
python -m venv .venv
.venv\Scripts\activate.bat
pip install -e .
h-agent init
```

### Windows Notes

1. **Python PATH**: Make sure to check "Add Python to PATH" during installation
2. **PowerShell Execution Policy**: If you encounter script running restrictions:
   ```powershell
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   ```
3. **Config file location**: `%APPDATA%\h-agent\`
4. **Port**: Windows uses TCP port (19527), not Unix Socket
5. **Chinese paths**: Project paths containing Chinese may cause encoding issues, use pure English paths

### Windows Dependency Issues

Some dependencies require compilation tools on Windows. If you encounter issues:

```powershell
# Install Visual Studio Build Tools (C++ build tools only)
# Or use precompiled wheels
pip install --only-binary :all: h-agent
```

---

## 4. Linux/macOS Installation

### Standard Installation

```bash
pip install h-agent
```

### Source Installation

```bash
git clone https://github.com/ekko-ai/h-agent.git
cd h-agent
pip install -e .

# Or install development version
pip install -e ".[dev]"
```

### macOS Apple Silicon (M1/M2/M3)

```bash
# Make sure to use ARM version of Python
 arch -arm64 /usr/bin/python3 -m pip install h-agent
```

---

## 5. Intranet/Offline Deployment

### Method 1: Offline pip Package

1. **Download on internet-connected machine**:

```bash
# Create offline package directory
mkdir h-agent-offline && cd h-agent-offline

# Download h-agent and all dependencies
pip download h-agent \
    --destination-dir . \
    --no-deps

# Recursively download dependencies (need to execute multiple times until no new packages)
pip download \
    openai python-dotenv pyyaml \
    --destination-dir . \
    --no-deps
```

2. **Transfer to intranet machine**:
   ```bash
   # Package
   tar -czvf h-agent-offline.tar.gz h-agent-offline/
   
   # Copy to intranet (USB/SMB/SCP, etc.)
   scp h-agent-offline.tar.gz user@intranet-server:/tmp/
   ```

3. **Install on intranet machine**:
   ```bash
   cd /tmp/h-agent-offline
   pip install --no-index --find-links=. h-agent
   ```

### Method 2: Virtual Environment Packaging

```bash
# On internet-connected machine
python -m venv h-agent-venv
source h-agent-venv/bin/activate
pip install h-agent

# Package virtual environment
tar -czvf h-agent-venv.tar.gz h-agent-venv/

# On intranet, extract and use
tar -xzf h-agent-venv.tar.gz
source h-agent-venv/bin/activate
h-agent init
```

### Intranet Configuration

When intranet cannot access OpenAI API, configure local model:

```bash
# Method 1: Ollama local model
h-agent config --base-url http://localhost:11434/v1
h-agent config --model llama3

# Method 2: Offline mirror (enterprise private model service)
h-agent config --base-url https://your-internal-model-server/v1
h-agent config --model your-internal-model
```

### Offline Verification

```bash
# Verify installation
h-agent --version

# Verify configuration (no API call needed)
h-agent config --show

# Test offline mode (assuming using Ollama)
ollama serve &
h-agent chat
```

---

## 6. Docker Deployment

### Run Using Docker

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app
RUN pip install h-agent

# Config file
COPY .env /root/.h-agent/.env

ENTRYPOINT ["h-agent", "start"]
```

```bash
# Build
docker build -t h-agent .

# Run
docker run -d \
    --name h-agent \
    -p 19527:19527 \
    -v ~/.h-agent:/root/.h-agent \
    -e OPENAI_API_KEY=sk-xxx \
    h-agent
```

### docker-compose Deployment

```yaml
version: '3.8'

services:
  h-agent:
    image: h-agent:latest
    container_name: h-agent
    ports:
      - "19527:19527"
    volumes:
      - ~/.h-agent:/root/.h-agent
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - OPENAI_BASE_URL=${OPENAI_BASE_URL}
      - MODEL_ID=${MODEL_ID}
    restart: unless-stopped
    networks:
      - h-agent-net

networks:
  h-agent-net:
    driver: bridge
```

```bash
# Start
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

---

## 7. Service Deployment

### systemd (Linux)

```ini
# ~/.config/systemd/user/h-agent.service
[Unit]
Description=h-agent Daemon
After=network.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 -m h_agent.daemon.server
Restart=on-failure
RestartSec=5
Environment="OPENAI_API_KEY=sk-xxx"
Environment="OPENAI_BASE_URL=https://api.openai.com/v1"

[Install]
WantedBy=default.target
```

```bash
# Reload systemd
systemctl --user daemon-reload

# Enable boot autostart
systemctl --user enable h-agent

# Start service
systemctl --user start h-agent

# View status
systemctl --user status h-agent
```

### launchd (macOS)

```xml
<!-- ~/Library/LaunchAgents/com.h-agent.daemon.plist -->
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.h-agent.daemon</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>-m</string>
        <string>h_agent.daemon.server</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>EnvironmentVariables</key>
    <dict>
        <key>OPENAI_API_KEY</key>
        <string>sk-xxx</string>
    </dict>
</dict>
</plist>
```

```bash
# Install
launchctl load ~/Library/LaunchAgents/com.h-agent.daemon.plist

# Uninstall
launchctl unload ~/Library/LaunchAgents/com.h-agent.daemon.plist
```

---

## 8. Proxy Configuration

### HTTP Proxy

```bash
# Set proxy environment variables
export HTTP_PROXY=http://proxy.example.com:8080
export HTTPS_PROXY=http://proxy.example.com:8080

# Or configure in .env
echo 'HTTP_PROXY=http://proxy.example.com:8080' >> ~/.h-agent/.env
echo 'HTTPS_PROXY=http://proxy.example.com:8080' >> ~/.h-agent/.env
```

### Programmatic Settings

```python
import os
os.environ["HTTP_PROXY"] = "http://proxy:8080"
os.environ["HTTPS_PROXY"] = "http://proxy:8080"

# Or use urllib
import urllib.request
proxy = urllib.request.ProxyHandler({'http': 'http://proxy:8080'})
opener = urllib.request.build_opener(proxy)
urllib.request.install_opener(opener)
```

---

## 9. FAQ

### Q: Installation error `Microsoft Visual C++ 14.0 is required`

**Solution**: Install precompiled wheel on Windows, or install [Visual Studio Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/).

### Q: `h-agent: command not found`

**Solution**: Check if pip installation path is in PATH:
```bash
python -m pip install h-agent
python -m h_agent --version
```

### Q: How to pass API Key for intranet deployment?

**Solution**: Use environment variables or `.env` file:
```bash
export OPENAI_API_KEY=sk-xxx
h-agent start
```

### Q: Can RAG functionality still be used in offline environment?

**Solution**: RAG's file indexing functionality is still available, but semantic search (vector retrieval) requires OpenAI API for generating embedding, not available offline.

### Q: Share configuration across multiple machines?

**Solution**: Specify config directory via `--config-dir`, or use NFS/sync tools to share `~/.h-agent/`.

---

## 10. Quick Verification

```bash
# 1. Verify version
h-agent --version

# 2. Initialize (if first time)
h-agent init

# 3. Check configuration
h-agent config --show

# 4. Start daemon
h-agent start
h-agent status

# 5. Test conversation
h-agent run "What is 1+1?"
```
