#!/usr/bin/env python3
"""测试 s03 任务规划"""

import os
import sys

os.environ["OPENAI_API_KEY"] = "0a0aef4f9ec64734a786b9f5b9632382.zjNnoTdYGDBBYnoS"
os.environ["OPENAI_BASE_URL"] = "https://open.bigmodel.cn/api/paas/v4"
os.environ["MODEL_ID"] = "glm-4-flash"

from s03_todo_write import agent_loop, todo_manager

def test_todo():
    print("测试 OpenAI Agent Harness - s03 任务规划")
    print("=" * 50)
    
    # 测试用例：让 agent 创建任务列表并执行
    messages = [{
        "role": "user",
        "content": """我需要你帮我完成一个简单的任务：
1. 创建一个 hello.txt 文件，内容是 "Hello from OpenAI Agent!"
2. 读取这个文件确认内容正确
3. 把内容改成 "Hello from Zoo Agent!"
4. 再次读取确认

先用 TodoWrite 记录这些任务，然后逐步执行。"""
    }]
    
    try:
        agent_loop(messages)
        
        print("\n" + "=" * 50)
        print("最终任务状态:")
        print(todo_manager.format_for_prompt())
        print("\n✅ 测试完成！")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_todo()