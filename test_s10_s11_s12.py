#!/usr/bin/env python3
"""测试 s10-s12"""

import os
os.environ["OPENAI_API_KEY"] = "0a0aef4f9ec64734a786b9f5b9632382.zjNnoTdYGDBBYnoS"
os.environ["OPENAI_BASE_URL"] = "https://open.bigmodel.cn/api/paas/v4"
os.environ["MODEL_ID"] = "glm-4-flash"

def test_s10():
    print("\n" + "=" * 50)
    print("测试 s10 - Team Protocols")
    print("=" * 50)
    
    from s10_team_protocols import ProtocolManager, RequestStatus
    
    pm = ProtocolManager()
    
    # 创建关闭请求
    req = pm.create_request("shutdown", "lead", "worker-1", {"reason": "maintenance"})
    print(f"创建请求: {req.request_id}, 状态: {req.status}")
    
    # 响应请求
    pm.respond(req.request_id, approve=True)
    print(f"响应后状态: {pm.requests[req.request_id].status}")
    
    assert pm.requests[req.request_id].status == RequestStatus.APPROVED
    print("✅ s10 测试通过")
    return True


def test_s11():
    print("\n" + "=" * 50)
    print("测试 s11 - Autonomous Agents")
    print("=" * 50)
    
    from s11_autonomous_agents import (
        AgentIdentity, TaskBoard, TaskStatus, read_messages, send_message, TASKS_DIR
    )
    import tempfile
    import shutil
    
    # 创建临时目录
    test_dir = tempfile.mkdtemp()
    tasks_dir = os.path.join(test_dir, ".tasks")
    os.makedirs(tasks_dir)
    
    try:
        # 测试身份
        identity = AgentIdentity(
            agent_id="test-agent",
            name="Test Agent",
            role="tester",
            team="qa",
            skills=["testing"],
        )
        print(f"身份: {identity.name} ({identity.role})")
        assert identity.agent_id == "test-agent"
        
        # 测试任务板
        tb = TaskBoard(Path(tasks_dir))
        task = tb.create_task("Test task", "This is a test")
        print(f"创建任务: {task.id}")
        
        # 认领任务
        claimed = tb.claim_task(task.id, "test-agent")
        assert claimed.status == TaskStatus.CLAIMED
        print(f"认领任务: {claimed.status}")
        
        # 完成任务
        completed = tb.complete_task(task.id, "Done!")
        assert completed.status == TaskStatus.COMPLETED
        print(f"完成任务: {completed.status}")
        
        print("✅ s11 测试通过")
        return True
    finally:
        shutil.rmtree(test_dir)


def test_s12():
    print("\n" + "=" * 50)
    print("测试 s12 - Worktree Task Isolation")
    print("=" * 50)
    
    from s12_worktree_task_isolation import (
        TaskManager, WorktreeManager, TaskStatus, TASKS_DIR, WORKTREES_DIR
    )
    import tempfile
    import shutil
    
    # 创建临时目录
    test_dir = tempfile.mkdtemp()
    tasks_dir = Path(test_dir) / ".tasks"
    worktrees_dir = Path(test_dir) / ".worktrees"
    tasks_dir.mkdir()
    worktrees_dir.mkdir()
    
    try:
        # 测试任务管理
        tm = TaskManager(tasks_dir)
        task = tm.create("Implement feature X", "Add new feature")
        print(f"创建任务: {task.id} - {task.subject}")
        
        # 测试 worktree 管理
        wm = WorktreeManager(worktrees_dir)
        worktree = wm.create("test-wt", task.id)
        print(f"创建 worktree: {worktree.name} at {worktree.path}")
        
        assert worktree.name == "test-wt"
        assert Path(worktree.path).exists()
        
        # 分配 worktree 到任务
        allocated = tm.allocate_worktree(task.id)
        print(f"分配 worktree: {allocated.name}")
        
        assert allocated.task_id == task.id
        
        # 列出 worktrees
        worktrees = wm.list()
        print(f"Worktrees: {len(worktrees)}")
        assert len(worktrees) == 1
        
        # 完成任务
        completed = tm.complete(task.id, "Feature implemented")
        print(f"完成任务: {completed.status}")
        
        # 清理 worktree
        wm.remove("test-wt")
        assert not Path(worktree.path).exists()
        print("Worktree 已删除")
        
        print("✅ s12 测试通过")
        return True
    finally:
        shutil.rmtree(test_dir)


if __name__ == "__main__":
    from pathlib import Path
    
    print("\n" + "=" * 50)
    print("OpenAI Agent Harness - s10/s11/s12 测试")
    print("=" * 50)
    
    results = []
    
    try:
        results.append(("s10", test_s10()))
    except Exception as e:
        print(f"❌ s10 失败: {e}")
        import traceback
        traceback.print_exc()
        results.append(("s10", False))
    
    try:
        results.append(("s11", test_s11()))
    except Exception as e:
        print(f"❌ s11 失败: {e}")
        import traceback
        traceback.print_exc()
        results.append(("s11", False))
    
    try:
        results.append(("s12", test_s12()))
    except Exception as e:
        print(f"❌ s12 失败: {e}")
        import traceback
        traceback.print_exc()
        results.append(("s12", False))
    
    print("\n" + "=" * 50)
    print("测试结果汇总")
    print("=" * 50)
    for name, passed in results:
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"  {name}: {status}")
    
    all_passed = all(r[1] for r in results)
    print("\n" + ("✅ 全部测试通过！" if all_passed else "❌ 有测试失败"))