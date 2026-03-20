#!/usr/bin/env python3
"""测试 s07-s09"""

import os
import json
os.environ["OPENAI_API_KEY"] = "0a0aef4f9ec64734a786b9f5b9632382.zjNnoTdYGDBBYnoS"
os.environ["OPENAI_BASE_URL"] = "https://open.bigmodel.cn/api/paas/v4"
os.environ["MODEL_ID"] = "glm-4-flash"

def test_s07():
    print("\n" + "=" * 50)
    print("测试 s07 - Task System")
    print("=" * 50)
    
    from s07_task_system import TaskManager, TaskStatus
    import tempfile
    
    # 使用临时文件
    tm = TaskManager(tempfile.NamedTemporaryFile(delete=False, suffix='.json').name)
    
    # 创建任务
    t1 = tm.create("实现登录功能", "用户登录模块", priority=3)
    t2 = tm.create("添加单元测试", "登录功能测试", priority=2, dependencies=[t1.id])
    t3 = tm.create("编写文档", "API文档", priority=1)
    
    print(f"\n创建了 {len(tm.tasks)} 个任务")
    
    # 测试依赖解析
    ready = tm.get_ready_tasks()
    print(f"就绪任务: {[t.id for t in ready]}")
    
    # 完成任务
    tm.start_task(t1.id)
    tm.complete_task(t1.id, "登录功能完成")
    
    # 再次检查就绪
    ready = tm.get_ready_tasks()
    print(f"完成 t1 后就绪: {[t.id for t in ready]}")
    
    # 测试图
    graph = tm.get_graph()
    print(f"任务图: {len(graph['nodes'])} nodes, {len(graph['edges'])} edges")
    
    print("✅ s07 测试通过")
    return True

def test_s08():
    print("\n" + "=" * 50)
    print("测试 s08 - Background Tasks")
    print("=" * 50)
    
    from s08_background_tasks import BackgroundTaskManager
    import time
    
    bg = BackgroundTaskManager()
    
    # 启动后台任务
    task = bg.spawn("sleep 2 && echo 'done'")
    print(f"启动后台任务: {task.id}")
    
    # 检查状态
    time.sleep(1)
    running = bg.get(task.id)
    print(f"1秒后状态: {running.status.value}")
    
    # 等待完成
    time.sleep(2)
    
    # 检查通知
    notifications = bg.get_notifications()
    print(f"通知: {notifications}")
    
    completed = bg.get(task.id)
    print(f"完成后状态: {completed.status.value}")
    
    print("✅ s08 测试通过")
    return True

def test_s09():
    print("\n" + "=" * 50)
    print("测试 s09 - Agent Teams")
    print("=" * 50)
    
    from s09_agent_teams import AgentTeam, AgentConfig, AgentRole, AgentMailbox
    import tempfile
    from pathlib import Path
    
    # 创建临时目录
    import shutil
    temp_dir = Path(tempfile.mkdtemp())
    
    team = AgentTeam()
    team.mailbox_dir = temp_dir
    team.task_file = temp_dir / "tasks.json"
    
    # 注册代理
    team.register_agent(AgentConfig(
        id="test-agent",
        name="Test Agent",
        role=AgentRole.WORKER,
    ))
    
    print(f"团队成员: {[a.name for a in team.list_agents()]}")
    
    # 发布任务
    task = team.post_task("测试任务", "这是一个测试")
    print(f"发布任务: {task['id']}")
    
    # 认领任务
    claimed = team.claim_task(task['id'], "test-agent")
    print(f"认领状态: {claimed['status']}")
    
    # 完成任务
    completed = team.complete_task(task['id'], "测试完成")
    print(f"完成状态: {completed['status']}")
    
    # 发送消息
    from s09_agent_teams import TeamMessage
    team.send_message(TeamMessage(
        id="msg-1",
        from_agent="lead",
        to_agent="test-agent",
        type="test",
        content="Hello",
    ))
    
    messages = team.get_messages("test-agent")
    print(f"收到消息: {len(messages)} 条")
    
    # 清理
    shutil.rmtree(temp_dir)
    
    print("✅ s09 测试通过")
    return True

if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("OpenAI Agent Harness - s07/s08/s09 测试")
    print("=" * 50)
    
    results = []
    
    try:
        results.append(("s07", test_s07()))
    except Exception as e:
        print(f"❌ s07 失败: {e}")
        results.append(("s07", False))
    
    try:
        results.append(("s08", test_s08()))
    except Exception as e:
        print(f"❌ s08 失败: {e}")
        results.append(("s08", False))
    
    try:
        results.append(("s09", test_s09()))
    except Exception as e:
        print(f"❌ s09 失败: {e}")
        results.append(("s09", False))
    
    print("\n" + "=" * 50)
    print("测试结果汇总")
    print("=" * 50)
    for name, passed in results:
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"  {name}: {status}")
    
    all_passed = all(r[1] for r in results)
    print("\n" + ("✅ 全部测试通过！" if all_passed else "❌ 有测试失败"))