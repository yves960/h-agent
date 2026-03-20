#!/usr/bin/env python3
"""测试 s01 agent loop"""

import os
import sys

# 设置测试环境
os.environ["OPENAI_API_KEY"] = "0a0aef4f9ec64734a786b9f5b9632382.zjNnoTdYGDBBYnoS"
os.environ["OPENAI_BASE_URL"] = "https://open.bigmodel.cn/api/paas/v4"
os.environ["MODEL_ID"] = "glm-4-flash"

from s01_agent_loop import agent_loop

def test_agent():
    print("测试 OpenAI Agent Harness - s01")
    print("-" * 40)
    
    # 测试用例 1: 简单的 bash 命令
    messages = [{"role": "user", "content": "用 ls 列出当前目录的文件，只需要执行命令"}]
    
    print("用户: 用 ls 列出当前目录的文件")
    print("-" * 40)
    
    try:
        agent_loop(messages)
        
        # 打印结果
        last = messages[-1]
        if last["role"] == "assistant":
            print("\n助手回复:")
            if last.get("content"):
                print(last["content"])
        print("\n✅ 测试通过！")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_agent()