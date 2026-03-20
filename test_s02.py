#!/usr/bin/env python3
"""测试 s02 多工具支持"""

import os
import sys

os.environ["OPENAI_API_KEY"] = "0a0aef4f9ec64734a786b9f5b9632382.zjNnoTdYGDBBYnoS"
os.environ["OPENAI_BASE_URL"] = "https://open.bigmodel.cn/api/paas/v4"
os.environ["MODEL_ID"] = "glm-4-flash"

from s02_tool_use import agent_loop

def test_multi_tool():
    print("测试 OpenAI Agent Harness - s02 多工具支持")
    print("=" * 50)
    
    # 测试用例: 创建文件、读取文件、编辑文件
    test_content = """# Test File

This is a test file.
Hello World!
"""
    
    # 删除旧的测试文件
    if os.path.exists("test_file.md"):
        os.remove("test_file.md")
    
    # 测试 1: 创建文件
    messages = [{
        "role": "user", 
        "content": "创建一个 test_file.md 文件，内容是 '# Test File\\n\\nThis is a test file.\\nHello World!'"
    }]
    
    print("\n测试 1: 写入文件")
    print("-" * 30)
    try:
        agent_loop(messages)
        print("✅ 写入测试通过")
    except Exception as e:
        print(f"❌ 写入测试失败: {e}")
        return
    
    # 测试 2: 读取文件
    messages = [{
        "role": "user", 
        "content": "读取 test_file.md 文件的内容"
    }]
    
    print("\n测试 2: 读取文件")
    print("-" * 30)
    try:
        agent_loop(messages)
        print("✅ 读取测试通过")
    except Exception as e:
        print(f"❌ 读取测试失败: {e}")
        return
    
    # 测试 3: 编辑文件
    messages = [{
        "role": "user", 
        "content": "把 test_file.md 中的 'Hello World!' 改成 'Hello Agent!'"
    }]
    
    print("\n测试 3: 编辑文件")
    print("-" * 30)
    try:
        agent_loop(messages)
        print("✅ 编辑测试通过")
    except Exception as e:
        print(f"❌ 编辑测试失败: {e}")
        return
    
    # 验证结果
    with open("test_file.md", "r") as f:
        final_content = f.read()
    
    if "Hello Agent!" in final_content:
        print("\n" + "=" * 50)
        print("✅ 所有测试通过！")
        print(f"\n最终文件内容:\n{final_content}")
    else:
        print(f"\n❌ 编辑验证失败，内容为:\n{final_content}")

if __name__ == "__main__":
    test_multi_tool()