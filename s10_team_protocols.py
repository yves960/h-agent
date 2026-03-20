#!/usr/bin/env python3
"""
s10_team_protocols.py - Team Protocols (OpenAI Version)

Structured handshakes between agents using request_id correlation.

Protocols:
1. Shutdown Protocol: Lead requests shutdown, teammates approve/reject
2. Plan Approval Protocol: Teammate submits plan, lead approves/rejects

Key insight: "Same request_id correlation pattern, two domains."
"""

import os
import json
import uuid
from datetime import datetime
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum

load_dotenv(override=True)

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY", "sk-dummy"),
    base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
)
MODEL = os.getenv("MODEL_ID", "gpt-4o")

WORK_DIR = Path.cwd()
TEAM_DIR = WORK_DIR / ".team"
TEAM_DIR.mkdir(exist_ok=True)

INBOX_DIR = TEAM_DIR / "inbox"
INBOX_DIR.mkdir(exist_ok=True)


# ============================================================
# Protocol Types
# ============================================================

class RequestStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


@dataclass
class ProtocolRequest:
    request_id: str
    request_type: str  # "shutdown" or "plan_approval"
    from_agent: str
    to_agent: str
    status: RequestStatus
    payload: Dict[str, Any]
    created_at: str
    responded_at: Optional[str] = None
    
    def to_dict(self) -> dict:
        d = asdict(self)
        d["status"] = self.status.value
        return d


class ProtocolManager:
    """Manages protocol requests and responses."""
    
    def __init__(self):
        self.requests: Dict[str, ProtocolRequest] = {}
        self._lock = None  # For thread safety in multi-agent env
    
    def create_request(
        self,
        request_type: str,
        from_agent: str,
        to_agent: str,
        payload: Dict[str, Any] = None,
    ) -> ProtocolRequest:
        """Create a new protocol request."""
        request = ProtocolRequest(
            request_id=f"req-{uuid.uuid4().hex[:8]}",
            request_type=request_type,
            from_agent=from_agent,
            to_agent=to_agent,
            status=RequestStatus.PENDING,
            payload=payload or {},
            created_at=datetime.now().isoformat(),
        )
        self.requests[request.request_id] = request
        return request
    
    def respond(
        self,
        request_id: str,
        approve: bool,
        response_payload: Dict[str, Any] = None,
    ) -> Optional[ProtocolRequest]:
        """Respond to a request."""
        if request_id not in self.requests:
            return None
        
        request = self.requests[request_id]
        request.status = RequestStatus.APPROVED if approve else RequestStatus.REJECTED
        request.responded_at = datetime.now().isoformat()
        if response_payload:
            request.payload.update(response_payload)
        
        return request
    
    def get_pending_for(self, agent_id: str) -> list:
        """Get pending requests for an agent."""
        return [
            r for r in self.requests.values()
            if r.to_agent == agent_id and r.status == RequestStatus.PENDING
        ]
    
    def get_pending_from(self, agent_id: str) -> list:
        """Get pending requests from an agent."""
        return [
            r for r in self.requests.values()
            if r.from_agent == agent_id and r.status == RequestStatus.PENDING
        ]


# Global protocol manager
protocol_manager = ProtocolManager()


# ============================================================
# Message Bus (JSONL inbox per agent)
# ============================================================

def send_message(to_agent: str, message: dict):
    """Send a message to an agent's inbox."""
    inbox_file = INBOX_DIR / f"{to_agent}.jsonl"
    with open(inbox_file, "a") as f:
        f.write(json.dumps(message) + "\n")


def read_messages(agent_id: str) -> list:
    """Read and clear messages from an agent's inbox."""
    inbox_file = INBOX_DIR / f"{agent_id}.jsonl"
    if not inbox_file.exists():
        return []
    
    messages = []
    with open(inbox_file, "r") as f:
        for line in f:
            if line.strip():
                messages.append(json.loads(line))
    
    # Clear inbox
    inbox_file.write_text("")
    return messages


# ============================================================
# Tools
# ============================================================

def tool_shutdown_request(to_agent: str, reason: str = "") -> str:
    """Request a shutdown from a teammate."""
    request = protocol_manager.create_request(
        request_type="shutdown",
        from_agent="lead",
        to_agent=to_agent,
        payload={"reason": reason},
    )
    
    # Send to teammate's inbox
    send_message(to_agent, {
        "type": "shutdown_request",
        "request_id": request.request_id,
        "from": "lead",
        "reason": reason,
    })
    
    return json.dumps({
        "request_id": request.request_id,
        "status": "pending",
        "message": f"Shutdown request sent to {to_agent}",
    })


def tool_shutdown_response(request_id: str, approve: bool, reason: str = "") -> str:
    """Respond to a shutdown request."""
    request = protocol_manager.respond(request_id, approve, {"reason": reason})
    if not request:
        return json.dumps({"error": "Request not found"})
    
    # Notify the requester
    send_message(request.from_agent, {
        "type": "shutdown_response",
        "request_id": request_id,
        "approve": approve,
        "reason": reason,
    })
    
    return json.dumps({
        "request_id": request_id,
        "status": request.status.value,
    })


def tool_plan_submit(to_agent: str, plan: str) -> str:
    """Submit a plan for approval."""
    request = protocol_manager.create_request(
        request_type="plan_approval",
        from_agent="worker",
        to_agent=to_agent,
        payload={"plan": plan},
    )
    
    send_message(to_agent, {
        "type": "plan_approval",
        "request_id": request.request_id,
        "from": "worker",
        "plan": plan,
    })
    
    return json.dumps({
        "request_id": request.request_id,
        "status": "pending",
        "message": f"Plan submitted to {to_agent}",
    })


def tool_plan_review(request_id: str, approve: bool, feedback: str = "") -> str:
    """Review and approve/reject a plan."""
    request = protocol_manager.respond(request_id, approve, {"feedback": feedback})
    if not request:
        return json.dumps({"error": "Request not found"})
    
    send_message(request.from_agent, {
        "type": "plan_approval_response",
        "request_id": request_id,
        "approve": approve,
        "feedback": feedback,
    })
    
    return json.dumps({
        "request_id": request_id,
        "status": request.status.value,
    })


def tool_check_protocols(agent_id: str) -> str:
    """Check for pending protocol requests."""
    pending = protocol_manager.get_pending_for(agent_id)
    return json.dumps({
        "pending_requests": [r.to_dict() for r in pending],
    })


def tool_read_messages(agent_id: str) -> str:
    """Read messages from inbox."""
    messages = read_messages(agent_id)
    return json.dumps({"messages": messages})


# Tool definitions
TOOLS = [
    {"type": "function", "function": {
        "name": "shutdown_request",
        "description": "Request a teammate to shutdown",
        "parameters": {
            "type": "object",
            "properties": {
                "to_agent": {"type": "string"},
                "reason": {"type": "string"},
            },
            "required": ["to_agent"],
        }
    }},
    {"type": "function", "function": {
        "name": "shutdown_response",
        "description": "Respond to a shutdown request",
        "parameters": {
            "type": "object",
            "properties": {
                "request_id": {"type": "string"},
                "approve": {"type": "boolean"},
                "reason": {"type": "string"},
            },
            "required": ["request_id", "approve"],
        }
    }},
    {"type": "function", "function": {
        "name": "plan_submit",
        "description": "Submit a plan for approval",
        "parameters": {
            "type": "object",
            "properties": {
                "to_agent": {"type": "string"},
                "plan": {"type": "string"},
            },
            "required": ["to_agent", "plan"],
        }
    }},
    {"type": "function", "function": {
        "name": "plan_review",
        "description": "Review and approve/reject a plan",
        "parameters": {
            "type": "object",
            "properties": {
                "request_id": {"type": "string"},
                "approve": {"type": "boolean"},
                "feedback": {"type": "string"},
            },
            "required": ["request_id", "approve"],
        }
    }},
    {"type": "function", "function": {
        "name": "check_protocols",
        "description": "Check for pending protocol requests",
        "parameters": {
            "type": "object",
            "properties": {
                "agent_id": {"type": "string"},
            },
            "required": ["agent_id"],
        }
    }},
    {"type": "function", "function": {
        "name": "read_messages",
        "description": "Read messages from inbox",
        "parameters": {
            "type": "object",
            "properties": {
                "agent_id": {"type": "string"},
            },
            "required": ["agent_id"],
        }
    }},
]

TOOL_HANDLERS = {
    "shutdown_request": tool_shutdown_request,
    "shutdown_response": tool_shutdown_response,
    "plan_submit": tool_plan_submit,
    "plan_review": tool_plan_review,
    "check_protocols": tool_check_protocols,
    "read_messages": tool_read_messages,
}


def execute_tool_call(tool_call) -> str:
    args = json.loads(tool_call.function.arguments)
    return TOOL_HANDLERS[tool_call.function.name](**args)


# ============================================================
# Agent Loop
# ============================================================

def get_system_prompt() -> str:
    return f"""You are a team lead at {WORK_DIR}.

Manage teammates with structured protocols:
- shutdown_request/response: Coordinate agent shutdown
- plan_submit/review: Approve or reject plans

Use check_protocols to see pending requests.
Use read_messages to check your inbox.

Act as a team coordinator."""


def agent_loop(messages: list):
    while True:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "system", "content": get_system_prompt()}] + messages,
            tools=TOOLS,
            tool_choice="auto",
            max_tokens=4000,
        )
        
        message = response.choices[0].message
        messages.append({"role": "assistant", "content": message.content, "tool_calls": message.tool_calls})
        
        if not message.tool_calls:
            return
        
        for tool_call in message.tool_calls:
            args = json.loads(tool_call.function.arguments)
            print(f"\033[34m🔄 {tool_call.function.name}: {args}\033[0m")
            
            result = execute_tool_call(tool_call)
            print(result[:150])
            
            messages.append({"role": "tool", "tool_call_id": tool_call.id, "content": result})


def main():
    print(f"\033[36mOpenAI Agent Harness - s10 (Team Protocols)\033[0m")
    print(f"Model: {MODEL}")
    print(f"Team dir: {TEAM_DIR}")
    print("\nProtocols: shutdown_request/response, plan_submit/review")
    print("\nType 'q' to quit\n")
    
    history = []
    while True:
        try:
            query = input("\033[36m>> \033[0m")
        except (EOFError, KeyboardInterrupt):
            break
        
        if query.strip().lower() == "q":
            break
        
        history.append({"role": "user", "content": query})
        agent_loop(history)
        
        if history[-1].get("content"):
            print(f"\n{history[-1]['content']}\n")


if __name__ == "__main__":
    main()