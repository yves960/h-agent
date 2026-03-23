#!/usr/bin/env python3
"""
h_agent/team/async_team.py - s09 Async Agent Teams Implementation

Persistent teammate threads with JSONL inbox-based communication.
Following learn-claude-code s09 pattern.
"""

import json
import os
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from h_agent.core.client import get_client
from h_agent.core.config import MODEL
from h_agent.logging_config import get_message_logger, get_llm_logger, trace

TEAM_DIR = Path(os.path.expanduser("~/.h-agent/team"))


class AsyncMessageBus:
    """File-based async message bus using JSONL inboxes."""
    
    def __init__(self, inbox_dir: Path = None):
        self.inbox_dir = inbox_dir or (TEAM_DIR / "inbox_async")
        self.inbox_dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
    
    def send(self, sender: str, to: str, content: str,
             msg_type: str = "message", **extra: Any) -> str:
        msg = {
            "type": msg_type,
            "from": sender,
            "content": content,
            "timestamp": time.time(),
        }
        msg.update(extra)
        
        inbox_path = self.inbox_dir / f"{to}.jsonl"
        
        with self._lock:
            with open(inbox_path, "a") as f:
                f.write(json.dumps(msg) + "\n")
        
        get_message_logger().log_message_sent(sender, to, msg_type, content)
        trace(f"[MESSAGE] {sender} → {to} ({msg_type}): {content[:100]}", "message")
        
        return f"Sent {msg_type} to {to}"
    
    def read_inbox(self, name: str) -> List[Dict]:
        inbox_path = self.inbox_dir / f"{name}.jsonl"
        
        if not inbox_path.exists():
            return []
        
        with self._lock:
            content = inbox_path.read_text()
            inbox_path.write_text("")
        
        if not content.strip():
            return []
        
        messages = []
        for line in content.strip().split("\n"):
            if line:
                try:
                    messages.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
        
        for msg in messages:
            get_message_logger().log_message_received(
                name, msg.get("from", "?"), msg.get("type", "?"), msg.get("content", "")
            )
        
        return messages
    
    def broadcast(self, sender: str, recipients: List[str], content: str,
                  msg_type: str = "broadcast") -> str:
        count = 0
        for name in recipients:
            if name != sender:
                self.send(sender, name, content, msg_type)
                count += 1
        return f"Broadcast to {count} teammates"


class TeammateManager:
    """Manages team lifecycle and teammate threads."""
    
    CONFIG_FILE = TEAM_DIR / "async_team_config.json"
    
    def __init__(self, team_id: str = "default", inbox_dir: Path = None):
        self.team_id = team_id
        self.inbox_dir = inbox_dir or (TEAM_DIR / "inbox_async")
        self.inbox_dir.mkdir(parents=True, exist_ok=True)
        self.config_path = self.CONFIG_FILE
        self.threads: Dict[str, threading.Thread] = {}
        self.statuses: Dict[str, str] = {}
        self.members: Dict[str, Dict] = {}
        self._lock = threading.Lock()
        self._shutdown_requested: Dict[str, bool] = {}
        self._load_config()
    
    def _load_config(self):
        if self.config_path.exists():
            try:
                config = json.loads(self.config_path.read_text())
                self.members = config.get("members", {})
            except (json.JSONDecodeError, IOError):
                self.members = {}
    
    def _save_config(self):
        config = {
            "team_id": self.team_id,
            "members": self.members,
        }
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        self.config_path.write_text(json.dumps(config, indent=2))
    
    def spawn(self, name: str, role: str, prompt: str,
              agent_handler: Any) -> str:
        if name in self.threads and self.statuses.get(name) == "working":
            return f"Error: '{name}' is already running"
        
        self._shutdown_requested[name] = False
        self.statuses[name] = "working"
        self.members[name] = {"role": role, "prompt": prompt, "status": "working"}
        self._save_config()
        
        thread = threading.Thread(
            target=_teammate_loop,
            args=(name, role, prompt, agent_handler, self),
            daemon=True,
        )
        self.threads[name] = thread
        thread.start()
        
        return f"Spawned '{name}' (role: {role})"
    
    def shutdown(self, name: str) -> str:
        self._shutdown_requested[name] = True
        self.statuses[name] = "shutdown"
        if name in self.members:
            self.members[name]["status"] = "shutdown"
        self._save_config()
        return f"Shutdown requested for '{name}'"
    
    def get_status(self, name: str) -> Optional[str]:
        return self.statuses.get(name)
    
    def list_members(self) -> List[Dict]:
        return [
            {"name": name, "role": self.members.get(name, {}).get("role", ""), "status": status}
            for name, status in self.statuses.items()
        ]
    
    def _set_status(self, name: str, status: str):
        with self._lock:
            self.statuses[name] = status
            if name in self.members:
                self.members[name]["status"] = status
        self._save_config()


def _execute_team_tool(tool_name: str, args: Dict, sender: str,
                      bus: AsyncMessageBus) -> str:
    if tool_name == "bash":
        import subprocess
        try:
            r = subprocess.run(
                args["command"], shell=True,
                capture_output=True, text=True, timeout=120
            )
            return (r.stdout + r.stderr).strip()[:50000] or "(no output)"
        except subprocess.TimeoutExpired:
            return "Error: Timeout (120s)"
        except Exception as e:
            return f"Error: {e}"
    
    elif tool_name == "read":
        try:
            path = Path(args["file_path"])
            text = path.read_text()
            limit = args.get("limit", 50000)
            return text[:limit] if len(text) > limit else text
        except Exception as e:
            return f"Error: {e}"
    
    elif tool_name == "write":
        try:
            path = Path(args["file_path"])
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(args["content"])
            return f"Wrote {len(args['content'])} bytes"
        except Exception as e:
            return f"Error: {e}"
    
    elif tool_name == "edit":
        try:
            path = Path(args["file_path"])
            content = path.read_text()
            if args["old_text"] not in content:
                return f"Error: Text not found in {args['file_path']}"
            content = content.replace(args["old_text"], args["new_text"], 1)
            path.write_text(content)
            return f"Edited {args['file_path']}"
        except Exception as e:
            return f"Error: {e}"
    
    elif tool_name == "send_message":
        return bus.send(sender, args["to"], args["content"], args.get("msg_type", "message"))
    
    elif tool_name == "read_inbox":
        return json.dumps(bus.read_inbox(sender), indent=2)
    
    return f"Unknown tool: {tool_name}"


TEAMMATE_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "bash",
            "description": "Run a shell command.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "The shell command to execute"}
                },
                "required": ["command"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read",
            "description": "Read file contents.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "Path to file"}
                },
                "required": ["file_path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "write",
            "description": "Write content to file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {"type": "string"},
                    "content": {"type": "string"}
                },
                "required": ["file_path", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "edit",
            "description": "Replace exact text in file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {"type": "string"},
                    "old_text": {"type": "string"},
                    "new_text": {"type": "string"}
                },
                "required": ["file_path", "old_text", "new_text"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "send_message",
            "description": "Send a message to a teammate.",
            "parameters": {
                "type": "object",
                "properties": {
                    "to": {"type": "string", "description": "Recipient teammate name"},
                    "content": {"type": "string", "description": "Message content"},
                    "msg_type": {"type": "string", "enum": ["message", "task", "broadcast"]}
                },
                "required": ["to", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_inbox",
            "description": "Read and drain your inbox.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
]


def _teammate_loop(name: str, role: str, prompt: str,
                   agent_handler: Any, manager: TeammateManager,
                   max_iterations: int = 50):
    """
    Persistent loop for teammate agent threads.
    
    Each iteration:
    1. Check shutdown signal
    2. Read inbox for new messages
    3. Process each message with LLM + tools
    4. Send response back to lead's inbox
    """
    client = get_client()
    messages = [{"role": "user", "content": prompt}]
    sys_prompt = f"You are '{name}', role: {role}. Use tools to communicate. Always respond to lead after completing tasks."
    
    idle_poll_interval = 5
    
    for iteration in range(max_iterations):
        if manager._shutdown_requested.get(name, False):
            manager._set_status(name, "shutdown")
            return
        
        bus = AsyncMessageBus()
        
        # Read all pending messages from inbox
        inbox = bus.read_inbox(name)
        if not inbox:
            manager._set_status(name, "idle")
            time.sleep(idle_poll_interval)
            continue
        
        manager._set_status(name, "working")
        
        # Process each message and collect responses
        for msg in inbox:
            msg_id = msg.get("id", f"msg-{iteration}")
            sender = msg.get("from", "lead")
            msg_type = msg.get("type", "message")
            
            # Add message to conversation context
            messages.append({
                "role": "user",
                "content": json.dumps(msg)
            })
            
            try:
                get_llm_logger().log_llm_request(
                    agent_name=f"[TEAMMATE]{name}",
                    messages_count=len(messages) + 1,
                    tools_count=len(TEAMMATE_TOOLS),
                    model=MODEL
                )
                trace(f"[{name}] Calling LLM with {len(messages)} messages", "teammate")
                
                response = client.chat.completions.create(
                    model=MODEL,
                    messages=[{"role": "system", "content": sys_prompt}] + messages,
                    tools=TEAMMATE_TOOLS,
                    max_tokens=8000,
                )
            except Exception as e:
                messages.append({
                    "role": "user",
                    "content": f"Error: {e}"
                })
                # Send error response back to lead
                bus.send(name, "lead", f"Error processing: {e}", 
                        msg_type="response", in_reply_to=msg_id)
                continue
            
            assistant_msg = response.choices[0].message
            response_content = assistant_msg.content or ""
            
            # Build tool calls for history
            tool_call_history = []
            if assistant_msg.tool_calls:
                messages.append({
                    "role": "assistant",
                    "content": response_content,
                    "tool_calls": [
                        {"id": tc.id, "type": "function",
                         "function": {"name": tc.function.name, "arguments": tc.function.arguments}}
                        for tc in assistant_msg.tool_calls
                    ]
                })
                
                # Execute each tool call
                for tc in assistant_msg.tool_calls:
                    args = json.loads(tc.function.arguments)
                    result = _execute_team_tool(tc.function.name, args, name, bus)
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": result
                    })
                    tool_call_history.append(f"{tc.function.name}: {result[:100]}")
            else:
                messages.append({
                    "role": "assistant",
                    "content": response_content,
                })
            
            # Send response back to lead
            final_content = response_content
            if tool_call_history:
                final_content = f"{response_content}\n\n[Tools used: {'; '.join(tool_call_history)}]"
            
            bus.send(name, "lead", final_content, 
                    msg_type="response", in_reply_to=msg_id)
    
    manager._set_status(name, "shutdown")


LEAD_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "send_message",
            "description": "Send a message to a teammate asynchronously.",
            "parameters": {
                "type": "object",
                "properties": {
                    "to": {"type": "string", "description": "Recipient teammate name"},
                    "content": {"type": "string", "description": "Message content"},
                    "msg_type": {"type": "string", "enum": ["message", "task", "broadcast"]}
                },
                "required": ["to", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "broadcast",
            "description": "Broadcast message to all teammates.",
            "parameters": {
                "type": "object",
                "properties": {
                    "content": {"type": "string", "description": "Message content to broadcast"}
                },
                "required": ["content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_teammates",
            "description": "List all teammates with their status.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_inbox",
            "description": "Read and drain your inbox.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "shutdown_teammate",
            "description": "Request a teammate to shutdown gracefully.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Teammate name to shutdown"}
                },
                "required": ["name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "spawn_teammate",
            "description": "Spawn a persistent autonomous teammate.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Name for the new teammate"},
                    "role": {"type": "string", "description": "Role of the teammate"},
                    "prompt": {"type": "string", "description": "System prompt for the teammate"}
                },
                "required": ["name", "role", "prompt"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "shutdown_request",
            "description": "Request a teammate to shut down via inbox message.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Teammate name to request shutdown"}
                },
                "required": ["name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "plan_approval",
            "description": "Approve or reject a teammate's plan.",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_id": {"type": "string", "description": "Task ID to approve/reject"},
                    "approve": {"type": "boolean", "description": "True to approve, False to reject"},
                    "feedback": {"type": "string", "description": "Optional feedback message"}
                },
                "required": ["task_id", "approve"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "idle",
            "description": "Enter idle state signaling no more work.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "claim_task",
            "description": "Claim a task from the board.",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_id": {"type": "string", "description": "Task ID to claim"}
                },
                "required": ["task_id"]
            }
        }
    },
]


class AsyncAgentTeam:
    """Async team wrapper providing talk_to_async and team coordination."""
    
    def __init__(self, team_id: str = "default"):
        self.team_id = team_id
        self.bus = AsyncMessageBus()
        self.manager = TeammateManager(team_id)
        self._spawned_agents: Dict[str, bool] = {}
    
    def spawn(self, name: str, role: str, prompt: str) -> str:
        """Spawn a teammate agent as a persistent thread."""
        if name in self._spawned_agents:
            thread = self.threads.get(name)
            if thread and thread.is_alive():
                return f"Agent '{name}' already spawned"
            del self._spawned_agents[name]
        
        self._spawned_agents[name] = True
        return self.manager.spawn(name, role, prompt, agent_handler=None)
    
    def talk_to_async(self, agent_name: str, message: str, timeout: float = 120) -> Dict:
        msg_id = f"lead-{time.time():.0f}-{id(message)}"
        self.bus.send("lead", agent_name, message, msg_type="dialog", id=msg_id)
        
        start = time.time()
        while time.time() - start < timeout:
            inbox = self.bus.read_inbox("lead")
            for msg in inbox:
                if msg.get("type") == "response" and msg.get("in_reply_to") == msg_id:
                    return {
                        "success": True,
                        "content": msg.get("content", ""),
                    }
            time.sleep(0.5)
        
        return {
            "success": False,
            "content": None,
            "error": f"Timeout waiting for response from {agent_name}"
        }
    
    def list_teammates(self) -> List[Dict]:
        return self.manager.list_members()
    
    def shutdown_teammate(self, name: str) -> str:
        self._spawned_agents.pop(name, None)
        return self.manager.shutdown(name)
    
    def shutdown_all(self):
        for name in list(self._spawned_agents.keys()):
            self.shutdown_teammate(name)
