#!/usr/bin/env python3
"""测试 s04 子代理功能"""

import os
import sys

os.environ["OPENAI_API_KEY"] = "0a0aef4f9ec64734a786b9f5b9632382.zjNnoTdYGDBBYnoS"
os.environ["OPENAI_BASE_URL"] = "https://open.bigmodel.cn/api/paas/v4"
os.environ["MODEL_ID"] = "glm-4-flash"

from s04_subagent import agent_loop, run_subagent, SubagentResult

def test_subagent_basic():
    """测试基础的子代理功能"""
    print("测试 s04 - Subagent 基础功能")
    print("=" * 50)
    
    # 测试 1: 直接调用子代理
    print("\n测试 1: 直接调用子代理")
    print("-" * 30)
    result = run_subagent(
        task="列出当前目录的所有 .py 文件，告诉我有多少个",
        context="当前在 openai-agent-harness 项目目录"
    )
    
    print(f"成功: {result.success}")
    print(f"步数: {result.steps}")
    print(f"结果: {result.content[:200]}")
    
    if result.success:
        print("✅ 子代理直接调用测试通过")
    else:
        print(f"❌ 子代理调用失败: {result.error}")
    
    # 测试 2: 通过主代理调用 delegate
    print("\n测试 2: 主代理使用 delegate 工具")
    print("-" * 30)
    
    messages = [{
        "role": "user",
        "content": "请用 delegate 工具让子代理帮我分析当前目录有哪些测试文件（test_*.py），并告诉我它们的功能"
    }]
    
    try:
        agent_loop(messages)
        print("\n✅ 主代理 delegate 测试完成")
    except Exception as e:
        print(f"❌ 测试失败: {e}")


if __name__ == "__main__":
    test_subagent_basic()