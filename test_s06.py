#!/usr/bin/env python3
"""测试 s06 上下文压缩"""

import os
os.environ["OPENAI_API_KEY"] = "0a0aef4f9ec64734a786b9f5b9632382.zjNnoTdYGDBBYnoS"
os.environ["OPENAI_BASE_URL"] = "https://open.bigmodel.cn/api/paas/v4"
os.environ["MODEL_ID"] = "glm-4-flash"

from s06_context_compact import ContextManager, context_manager

def test_context_compact():
    print("测试 s06 - Context Compact")
    print("=" * 50)
    
    # 测试 1: 上下文计数
    print("\n测试 1: Token 估算")
    messages = [
        {"role": "user", "content": "Hello" * 100},
        {"role": "assistant", "content": "Hi" * 50},
        {"role": "user", "content": "Test" * 200},
    ]
    tokens = context_manager.count_tokens_estimate(messages)
    print(f"Est. tokens: {tokens}")
    assert tokens > 0
    print("✅ Token 估算通过")
    
    # 测试 2: 工具结果截断
    print("\n测试 2: 工具结果截断")
    cm = ContextManager(max_tool_result_chars=100)
    long_result = "x" * 1000
    messages = [{"role": "tool", "content": long_result, "tool_call_id": "1"}]
    truncated = cm.truncate_tool_results(messages)
    assert len(truncated[0]["content"]) < 200  # 包含截断标记
    print(f"Original: {len(long_result)} chars")
    print(f"Truncated: {len(truncated[0]['content'])} chars")
    print("✅ 截断测试通过")
    
    # 测试 3: 压缩判断
    print("\n测试 3: 压缩判断")
    cm2 = ContextManager(max_messages=10)
    many_messages = [{"role": "user", "content": f"msg{i}"} for i in range(15)]
    assert cm2.should_compact(many_messages)
    print(f"Should compact 15 messages (max 10): {cm2.should_compact(many_messages)}")
    print("✅ 压缩判断通过")
    
    # 测试 4: 摘要生成
    print("\n测试 4: 摘要生成")
    summary = context_manager.generate_summary(many_messages)
    print(f"Summary:\n{summary[:200]}...")
    assert "Conversation" in summary
    print("✅ 摘要测试通过")
    
    # 测试 5: 检查点保存和加载
    print("\n测试 5: 检查点保存")
    test_messages = [{"role": "user", "content": "test"}]
    context_manager.save_checkpoint(test_messages, "test_thread")
    
    loaded = context_manager.load_checkpoint("test_thread")
    assert loaded == test_messages
    print("✅ 检查点测试通过")
    
    print("\n" + "=" * 50)
    print("✅ 所有测试通过！")

if __name__ == "__main__":
    test_context_compact()