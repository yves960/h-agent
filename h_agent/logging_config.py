"""
h_agent/logging_config.py - Centralized logging configuration for h-agent

Log Directory: ~/.h-agent/logs/
"""

import os
import logging
import json
from pathlib import Path
from datetime import datetime
from typing import Optional
from logging.handlers import RotatingFileHandler


# ============================================================
# Log Directory
# ============================================================

def get_log_dir() -> Path:
    """Get the log directory, defaulting to ~/.h-agent/logs/"""
    log_dir = Path(os.getenv("H_AGENT_LOG_DIR", str(Path.home() / ".h-agent" / "logs")))
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir


LOG_DIR = get_log_dir()


# ============================================================
# Log Files
# ============================================================

def get_llm_log_file() -> Path:
    """LLM API call log"""
    return LOG_DIR / "llm_calls.jsonl"

def get_agent_log_file() -> Path:
    """Agent interaction log"""
    return LOG_DIR / "agent_interactions.jsonl"

def get_message_log_file() -> Path:
    """Inter-agent message log"""
    return LOG_DIR / "messages.jsonl"

def get_trace_log_file() -> Path:
    """General trace log (text format for debugging)"""
    return LOG_DIR / "trace.log"


# ============================================================
# JSONL Logger - for structured LLM/agent logs
# ============================================================

class JSONLLogger:
    """Append-only JSONL logger for LLM calls and agent interactions"""
    
    def __init__(self, file_path: Path):
        self.file_path = file_path
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
    
    def log(self, event_type: str, data: dict):
        """Log a JSON event"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "type": event_type,
            "data": data
        }
        with open(self.file_path, "a") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    
    def log_llm_request(self, agent_name: str, messages_count: int, tools_count: int, model: str):
        """Log LLM API request"""
        self.log("llm_request", {
            "agent": agent_name,
            "messages_count": messages_count,
            "tools_count": tools_count,
            "model": model
        })
    
    def log_llm_response(self, agent_name: str, response_preview: str, tool_calls_count: int):
        """Log LLM API response"""
        self.log("llm_response", {
            "agent": agent_name,
            "response_preview": response_preview[:200] if response_preview else "",
            "tool_calls_count": tool_calls_count
        })
    
    def log_tool_call(self, agent_name: str, tool_name: str, args: dict, result_preview: str):
        """Log tool call execution"""
        self.log("tool_call", {
            "agent": agent_name,
            "tool": tool_name,
            "args": args,
            "result_preview": result_preview[:500] if result_preview else ""
        })
    
    def log_message_sent(self, sender: str, to: str, msg_type: str, content_preview: str):
        """Log inter-agent message sent"""
        self.log("message_sent", {
            "from": sender,
            "to": to,
            "type": msg_type,
            "content_preview": content_preview[:200] if content_preview else ""
        })
    
    def log_message_received(self, receiver: str, from_sender: str, msg_type: str, content_preview: str):
        """Log inter-agent message received"""
        self.log("message_received", {
            "receiver": receiver,
            "from": from_sender,
            "type": msg_type,
            "content_preview": content_preview[:200] if content_preview else ""
        })


# ============================================================
# Global Logger Instances
# ============================================================

_llm_logger: Optional[JSONLLogger] = None
_agent_logger: Optional[JSONLLogger] = None
_message_logger: Optional[JSONLLogger] = None
_trace_logger: Optional[logging.Logger] = None


def get_llm_logger() -> JSONLLogger:
    """Get the LLM logger instance"""
    global _llm_logger
    if _llm_logger is None:
        _llm_logger = JSONLLogger(get_llm_log_file())
    return _llm_logger


def get_agent_logger() -> JSONLLogger:
    """Get the agent logger instance"""
    global _agent_logger
    if _agent_logger is None:
        _agent_logger = JSONLLogger(get_agent_log_file())
    return _agent_logger


def get_message_logger() -> JSONLLogger:
    """Get the message logger instance"""
    global _message_logger
    if _message_logger is None:
        _message_logger = JSONLLogger(get_message_log_file())
    return _message_logger


def get_trace_logger() -> logging.Logger:
    """Get a text-based trace logger for general debugging"""
    global _trace_logger
    if _trace_logger is None:
        _trace_logger = logging.getLogger("h_agent.trace")
        _trace_logger.setLevel(logging.DEBUG)
        
        # File handler
        trace_file = get_trace_log_file()
        file_handler = RotatingFileHandler(
            trace_file, maxBytes=10*1024*1024, backupCount=5
        )
        file_handler.setLevel(logging.DEBUG)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Format
        formatter = logging.Formatter(
            '%(asctime)s [%(name)s] %(levelname)s: %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        _trace_logger.addHandler(file_handler)
        _trace_logger.addHandler(console_handler)
    
    return _trace_logger


# ============================================================
# Convenience Functions
# ============================================================

def log_llm_call(agent_name: str, messages: list, tools: list, model: str,
                 response_content: str = None, tool_calls: list = None):
    """Log a complete LLM interaction"""
    llm = get_llm_logger()
    
    # Log request
    llm.log_llm_request(
        agent_name=agent_name,
        messages_count=len(messages),
        tools_count=len(tools) if tools else 0,
        model=model
    )
    
    # Log response
    if response_content is not None or tool_calls:
        tc_count = len(tool_calls) if tool_calls else 0
        preview = response_content[:200] if response_content else f"[{tc_count} tool_calls]"
        llm.log_llm_response(agent_name, preview, tc_count)


def log_interaction(agent_name: str, event: str, data: dict):
    """Log an agent interaction event"""
    agent = get_agent_logger()
    agent.log(event, {"agent": agent_name, **data})


def trace(message: str, category: str = "general"):
    """Quick trace logging"""
    logger = get_trace_logger()
    logger.debug(f"[{category}] {message}")


# ============================================================
# Initialize on Import
# ============================================================

def init_logging():
    """Initialize logging directories"""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    
    # Touch log files to ensure they exist
    get_llm_log_file().parent.mkdir(parents=True, exist_ok=True)
    get_llm_log_file().touch()
    get_agent_log_file().touch()
    get_message_log_file().touch()
    get_trace_log_file().touch()
    
    return LOG_DIR


# Auto-init on import
try:
    _init_log_dir = init_logging()
except Exception:
    pass
