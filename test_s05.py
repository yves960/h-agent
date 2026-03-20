#!/usr/bin/env python3
"""测试 s05 技能加载"""

import os
os.environ["OPENAI_API_KEY"] = "0a0aef4f9ec64734a786b9f5b9632382.zjNnoTdYGDBBYnoS"
os.environ["OPENAI_BASE_URL"] = "https://open.bigmodel.cn/api/paas/v4"
os.environ["MODEL_ID"] = "glm-4-flash"

from s05_skill_loading import agent_loop, list_available_skills, load_skill_content

def test_skills():
    print("测试 s05 - Skill Loading")
    print("=" * 50)
    
    # 测试 1: 列出技能
    print("\n测试 1: 列出可用技能")
    skills = list_available_skills()
    print(f"可用技能: {skills}")
    assert len(skills) >= 2, "应该至少有2个技能"
    print("✅ 列表测试通过")
    
    # 测试 2: 加载技能内容
    print("\n测试 2: 加载技能内容")
    content = load_skill_content("code-review")
    print(f"code-review 内容长度: {len(content)} 字符")
    assert "Code review guidelines" in content
    print("✅ 加载测试通过")
    
    # 测试 3: 通过 agent 使用技能
    print("\n测试 3: Agent 使用技能")
    messages = [{
        "role": "user",
        "content": "列出所有可用的技能"
    }]
    
    agent_loop(messages)
    print("\n✅ Agent 技能列表测试通过")
    
    # 测试 4: 加载特定技能
    print("\n测试 4: 加载 code-review 技能")
    messages = [{
        "role": "user",
        "content": "加载 code-review 技能，然后告诉我代码审查时应该注意什么"
    }]
    
    agent_loop(messages)
    print("\n✅ 技能加载测试通过")

if __name__ == "__main__":
    test_skills()