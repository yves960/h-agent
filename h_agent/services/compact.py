"""
h_agent/services/compact.py - Message Compaction Service

Provides functionality to compress conversation history
while preserving key information.
"""

from typing import List

from h_agent.core.client import get_client


async def compact_messages(messages: List[dict], max_tokens: int = 4000) -> List[dict]:
    """
    Compress conversation history while preserving key information.
    
    Strategy:
    1. Preserve system messages
    2. Keep recent N messages
    3. Generate summary for older messages
    
    Args:
        messages: List of message dicts
        max_tokens: Target token budget (not strictly enforced)
        
    Returns:
        Compacted message list
    """
    if not messages:
        return messages
    
    result = []
    
    # Preserve system messages
    for msg in messages:
        if msg.get("role") == "system":
            result.append(msg)
    
    # Keep recent messages
    recent = messages[-10:]  # Last 10 messages
    
    # Generate summary for older messages if there are any
    older = messages[:-10]
    if older:
        summary = await generate_summary(older)
        result.append({
            "role": "system",
            "content": f"[Earlier conversation summary]\n{summary}"
        })
    
    result.extend(recent)
    return result


async def generate_summary(messages: List[dict]) -> str:
    """
    Generate a summary of older messages using LLM.
    
    Args:
        messages: List of message dicts to summarize
        
    Returns:
        Summary string
    """
    if not messages:
        return ""
    
    # Format messages for the prompt
    msg_texts = []
    for msg in messages:
        role = msg.get("role", "unknown")
        content = msg.get("content", "")
        if isinstance(content, list):
            content = " ".join(c.get("text", str(c)) for c in content if isinstance(c, dict))
        msg_texts.append(f"{role}: {content[:200]}")
    
    full_text = "\n".join(msg_texts[:50])  # Limit to first 50 messages
    
    prompt = f"""Summarize this conversation concisely, preserving key information:
- Important decisions made
- Open questions or unresolved issues
- User preferences or context

Conversation:
{full_text[:3000]}

Provide a brief 2-3 sentence summary."""

    try:
        client = get_client()
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant that summarizes conversations concisely."
                },
                {
                    "role": "user", 
                    "content": prompt
                }
            ],
            max_tokens=200,
            temperature=0.3,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"[Summary unavailable: {e}]"
