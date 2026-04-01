#!/usr/bin/env python3
"""
h-agent 团队工作流测试脚本

测试场景：
1. 初始化6角色Agent团队
2. 用户向组长Agent下达任务
3. 组长Agent委托给各Agent工作
4. 各Agent汇报结果给组长
5. 组长向用户汇总

运行方式：
    python test_team_workflow.py
"""

import json
from h_agent.team.team import AgentTeam, AgentRole, TeamMessage, TaskResult
from h_agent.core.client import get_client
from h_agent.core.config import MODEL

# ============================================================
# 定义各Agent的系统提示
# ============================================================

PROMPTS = {
    "组长": """你是一个技术团队组长，负责协调团队工作。

你的团队成员：
- 产品：负责需求调研和分析，输出PRD
- 架构：负责技术方案设计
- 开发：负责代码实现
- 测试：负责测试验证
- 运维：负责部署和运维

工作流程：
1. 接收用户需求
2. 通过 delegate() 委托任务给相关Agent
3. 收集各Agent的工作结果
4. 向用户汇报进展和结果

你可以使用：
- delegate(agent_name, task_type, task_content) 委托任务
- query(agent_name, query) 查询Agent状态
- talk_to(agent_name, message) 与Agent对话

当用户提出任务时，你应该分解任务，然后委托给合适的Agent。""",

    "产品": """你是一个资深产品经理，负责需求调研和分析。

工作流程：
1. 接收组长委托的需求调研任务
2. 分析需求，输出产品文档（PRD格式）
3. 包含：需求背景、功能列表、用户故事、优先级

你是一个专业的分析师，会深入理解需求并给出清晰的需求文档。""",

    "架构": """你是一个资深架构师，负责技术方案设计。

工作流程：
1. 接收组长委托的架构设计任务
2. 根据需求输出技术方案
3. 包含：技术选型、系统设计、接口设计、数据库设计

你注重方案的实用性、可扩展性和可维护性。""",

    "开发": """你是一个资深开发工程师，负责代码实现。

工作流程：
1. 接收组长委托的开发任务
2. 参考架构方案进行编码
3. 完成后通过 delegate("测试", "测试", "测试内容") 通知测试Agent
4. 如果测试失败，修复问题后重新测试
5. 测试通过后向组长汇报完成

你可以使用 bash 工具执行命令、read/write/edit 操作文件。""",

    "测试": """你是一个资深测试工程师，负责测试验证。

工作流程：
1. 等待开发Agent发来的测试任务
2. 编写测试用例
3. 执行测试
4. 返回测试结果（通过/失败及原因）

你是一个严谨的测试工程师，不放过任何问题。""",

    "运维": """你是一个资深运维工程师，负责部署和运维。

工作流程：
1. 接收组长委托的运维任务
2. 输出部署方案或运维建议
3. 汇报结果给组长

你注重稳定性、安全性和可观测性。"""
}

# ============================================================
# 创建Agent Handler
# ============================================================

def create_handler(name: str, prompt: str):
    """为每个Agent创建LLM handler"""
    
    def handler(msg: TeamMessage) -> TaskResult:
        try:
            client = get_client()
            
            # 构造消息
            messages = [
                {"role": "system", "content": prompt},
                {"role": "user", "content": f"任务类型: {msg.type}\n任务内容: {msg.content}"}
            ]
            
            # 调用LLM
            response = client.chat.completions.create(
                model=MODEL,
                messages=messages,
                max_tokens=2048,
            )
            
            content = response.choices[0].message.content
            
            return TaskResult(
                agent_name=name,
                role=AgentRole.COORDINATOR,  # 实际应该根据角色来
                success=True,
                content=content,
            )
        except Exception as e:
            return TaskResult(
                agent_name=name,
                role=AgentRole.COORDINATOR,
                success=False,
                content=None,
                error=str(e),
            )
    
    return handler

# ============================================================
# 初始化团队
# ============================================================

def init_team() -> AgentTeam:
    """初始化6角色Agent团队"""
    team = AgentTeam(team_id="dev-team")
    
    # 注册6个Agent
    role_map = {
        "组长": AgentRole.COORDINATOR,
        "产品": AgentRole.RESEARCHER,
        "架构": AgentRole.PLANNER,
        "开发": AgentRole.CODER,
        "测试": AgentRole.REVIEWER,
        "运维": AgentRole.DEVOPS,
    }
    
    for name, role in role_map.items():
        team.register(
            name=name,
            role=role,
            handler=create_handler(name, PROMPTS[name]),
            description=f"{name}Agent",
        )
        print(f"✓ 注册 {name}Agent ({role.value})")
    
    return team

# ============================================================
# 测试用例
# ============================================================

def test_workflow(team: AgentTeam):
    """测试完整工作流"""
    
    print("\n" + "="*60)
    print("开始测试：用户向组长下达任务")
    print("="*60 + "\n")
    
    # 用户需求
    user_request = "帮我开发一个用户登录功能"
    
    print(f"👤 用户: {user_request}\n")
    
    # Step 1: 组长接收需求，分析并委托
    print("-"*40)
    print("📋 组长分析需求，开始委托任务...")
    print("-"*40)
    
    # 组长委托产品调研
    print("\n🔍 组长委托 产品Agent 进行需求调研...")
    product_result = team.delegate("产品", "需求调研", user_request)
    print(f"📄 产品Agent 结果:\n{product_result.content[:500]}...")
    
    # 组长委托架构设计
    print("\n📐 组长委托 架构Agent 进行方案设计...")
    arch_result = team.delegate("架构", "方案设计", f"需求：{user_request}\n\n产品分析：{product_result.content}")
    print(f"🏗️ 架构Agent 结果:\n{arch_result.content[:500]}...")
    
    # 组长委托开发
    print("\n💻 组长委托 开发Agent 进行编码...")
    dev_result = team.delegate("开发", "开发", f"需求：{user_request}\n\n产品分析：{product_result.content}\n\n架构方案：{arch_result.content}")
    print(f"🔧 开发Agent 结果:\n{dev_result.content[:500]}...")
    
    # Step 2: 开发通知测试
    print("\n" + "-"*40)
    print("🧪 开发Agent 通知 测试Agent 进行测试...")
    print("-"*40)
    
    test_result = team.delegate("测试", "测试", "测试登录功能，参考开发Agent的实现")
    print(f"✅ 测试Agent 结果:\n{test_result.content[:500]}...")
    
    # Step 3: 组长汇总
    print("\n" + "="*60)
    print("📊 组长向用户汇总")
    print("="*60)
    
    summary = f"""
任务完成汇报：

1. 需求分析（产品Agent）：
{product_result.content[:300]}

2. 技术方案（架构Agent）：
{arch_result.content[:300]}

3. 代码实现（开发Agent）：
{dev_result.content[:300]}

4. 测试结果（测试Agent）：
{test_result.content}

✅ 登录功能开发完成！
"""
    print(summary)

def test_query_and_correct(team: AgentTeam):
    """测试组长查询和纠正能力"""
    
    print("\n" + "="*60)
    print("测试：组长查询和纠正Agent")
    print("="*60 + "\n")
    
    # 查询测试Agent状态
    print("🔍 组长查询 测试Agent 状态...")
    status = team.query("测试", "你最近测试了什么功能？")
    print(f"📋 测试Agent 回复: {status.content}")
    
    # 组长纠正开发Agent
    print("\n📝 组长通知 开发Agent 修正代码...")
    correct = team.talk_to("开发", "你之前的登录实现有个bug：密码没有加密。请修复这个问题。")
    print(f"🔧 开发Agent 回复: {correct.content}")

# ============================================================
# 主函数
# ============================================================

def main():
    print("🚀 初始化Agent团队...")
    team = init_team()
    
    print("\n团队成员:")
    for m in team.list_members():
        print(f"  - {m['name']} ({m['role']})")
    
    # 测试1: 完整工作流
    test_workflow(team)
    
    # 测试2: 查询和纠正
    test_query_and_correct(team)
    
    print("\n✅ 测试完成！")

if __name__ == "__main__":
    main()
