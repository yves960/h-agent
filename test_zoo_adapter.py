#!/usr/bin/env python3
"""测试 Zoo 适配器"""

import os
import sys
import asyncio

os.environ["OPENAI_API_KEY"] = "0a0aef4f9ec64734a786b9f5b9632382.zjNnoTdYGDBBYnoS"
os.environ["OPENAI_BASE_URL"] = "https://open.bigmodel.cn/api/paas/v4"
os.environ["MODEL_ID"] = "glm-4-flash"

from zoo_adapter import OpenAIAgentService, AnimalMessage

async def test_zoo_adapter():
    print("测试 Zoo 适配器")
    print("=" * 50)
    
    # 创建服务
    service = OpenAIAgentService(
        animal_id="openai",
        model="glm-4-flash",
    )
    
    print(f"Agent ID: {service.animal_id}")
    print(f"Agent 信息: {service.get_animal_info()}")
    print("-" * 50)
    
    # 测试 invoke 方法
    prompt = "列出当前目录的 Python 文件，告诉我有几个"
    
    print(f"\n用户: {prompt}")
    print("-" * 50)
    
    message_count = 0
    async for msg in service.invoke(prompt, "test-thread"):
        message_count += 1
        print(f"[{msg.message_type}] {msg.content[:100]}{'...' if len(msg.content) > 100 else ''}")
        
        if msg.is_complete:
            break
    
    print("-" * 50)
    print(f"收到 {message_count} 条消息")
    print("✅ Zoo 适配器测试通过！")

if __name__ == "__main__":
    asyncio.run(test_zoo_adapter())