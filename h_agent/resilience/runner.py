#!/usr/bin/env python3

import time
from typing import Optional, List, Tuple, Any, Callable
from dataclasses import dataclass

from h_agent.resilience.classify import FailoverReason, classify_failure, get_cooldown
from h_agent.resilience.profiles import ProfileManager, AuthProfile

BASE_RETRY = 24
PER_PROFILE = 8
MAX_OVERFLOW_COMPACTION = 2

@dataclass
class ResilienceResult:
    success: bool
    content: Any
    error: Optional[str] = None
    retries: int = 0
    profile_used: Optional[str] = None

class ResilienceRunner:
    def __init__(
        self,
        profile_manager: ProfileManager,
        model: str = "gpt-4o",
        fallback_models: Optional[List[str]] = None,
        max_iterations: int = 50,
    ):
        self.profile_manager = profile_manager
        self.model = model
        self.fallback_models = fallback_models or []
        self.max_iterations = max_iterations
        self.total_retries = 0
    
    def run(
        self,
        system: str,
        messages: List[dict],
        tools: List[dict],
        api_client_fn: Callable[[str, str], Any],
    ) -> ResilienceResult:
        for rotation in range(len(self.profile_manager.profiles)):
            profile = self.profile_manager.select_profile()
            if profile is None:
                break
            
            api_client = api_client_fn(profile.api_key, profile.api_base)
            layer2_messages = list(messages)
            
            for compact_attempt in range(MAX_OVERFLOW_COMPACTION):
                try:
                    result, layer2_messages = self._run_attempt(
                        api_client, self.model, system, layer2_messages, tools
                    )
                    self.profile_manager.mark_success(profile)
                    return ResilienceResult(
                        success=True,
                        content=result,
                        retries=self.total_retries,
                        profile_used=profile.name,
                    )
                
                except Exception as exc:
                    reason = classify_failure(exc)
                    
                    if reason == FailoverReason.overflow:
                        layer2_messages = self._truncate_tool_results(layer2_messages)
                        layer2_messages = self._compact_history(layer2_messages, api_client)
                        continue
                    
                    elif reason in (FailoverReason.auth, FailoverReason.rate_limit, FailoverReason.billing):
                        self.profile_manager.mark_failure(profile, reason)
                        break
                    
                    elif reason == FailoverReason.timeout:
                        self.profile_manager.mark_failure(profile, reason, 60)
                        break
                    
                    else:
                        self.total_retries += 1
                        if self.total_retries >= BASE_RETRY:
                            break
        
        for fallback_model in self.fallback_models:
            profile = self.profile_manager.select_profile()
            if profile is None:
                continue
            try:
                api_client = api_client_fn(profile.api_key, profile.api_base)
                result, _ = self._run_attempt(
                    api_client, fallback_model, system, messages, tools
                )
                return ResilienceResult(
                    success=True,
                    content=result,
                    retries=self.total_retries,
                    profile_used=profile.name,
                )
            except Exception:
                continue
        
        return ResilienceResult(
            success=False,
            content=None,
            error="all profiles and fallbacks exhausted",
            retries=self.total_retries,
        )
    
    def _run_attempt(
        self,
        api_client: Any,
        model: str,
        system: str,
        messages: List[dict],
        tools: List[dict],
    ) -> Tuple[Any, List[dict]]:
        current_messages = list(messages)
        iteration = 0
        
        while iteration < self.max_iterations:
            iteration += 1
            
            response = api_client.chat.completions.create(
                model=model,
                max_tokens=4096,
                messages=[{"role": "system", "content": system}] + current_messages,
                tools=tools,
            )
            
            current_messages.append({
                "role": "assistant",
                "content": response.choices[0].message.content,
                "tool_calls": getattr(response.choices[0].message, "tool_calls", None),
            })
            
            if not response.choices[0].message.tool_calls:
                return response, current_messages
            
            tool_results = []
            for tc in response.choices[0].message.tool_calls:
                result = self._execute_tool(tc.function.name, tc.function.arguments)
                tool_results.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": result,
                })
            current_messages.append({"role": "user", "content": tool_results})
        
        raise RuntimeError("Tool-use loop exceeded max iterations")
    
    def _execute_tool(self, name: str, arguments: str) -> str:
        return f"Tool {name} executed"
    
    def _truncate_tool_results(self, messages: List[dict]) -> List[dict]:
        max_result_size = 10000
        truncated = []
        for msg in messages:
            if msg.get("role") == "user" and isinstance(msg.get("content"), list):
                new_content = []
                for block in msg["content"]:
                    if block.get("type") == "tool_result":
                        result = block.get("content", "")
                        if len(result) > max_result_size:
                            block = {**block, "content": result[:max_result_size] + "...[truncated]"}
                    new_content.append(block)
                truncated.append({**msg, "content": new_content})
            else:
                truncated.append(msg)
        return truncated
    
    def _compact_history(self, messages: List[dict], api_client: Any) -> List[dict]:
        if len(messages) < 10:
            return messages
        
        keep_count = max(4, int(len(messages) * 0.2))
        compress_count = max(2, int(len(messages) * 0.5))
        compress_count = min(compress_count, len(messages) - keep_count)
        
        old_messages = messages[:compress_count]
        old_text = "\n".join([
            f"{m.get('role', 'user')}: {m.get('content', '')}"
            for m in old_messages
        ])
        
        summary_prompt = f"Summarize this conversation concisely, preserving key facts:\n\n{old_text[:8000]}"
        
        summary_response = api_client.chat.completions.create(
            model=self.model,
            max_tokens=1024,
            messages=[
                {"role": "system", "content": "You are a conversation summarizer. Be concise."},
                {"role": "user", "content": summary_prompt},
            ],
        )
        
        summary = summary_response.choices[0].message.content
        
        compacted = [
            {"role": "user", "content": f"[Previous conversation summary]\n{summary}"},
            {"role": "assistant", "content": "Understood, I have the context."},
        ]
        compacted.extend(messages[compress_count:])
        return compacted