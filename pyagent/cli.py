#!/usr/bin/env python3
"""
OpenAI Agent Harness - 命令行入口
"""

import argparse
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(
        description="OpenAI Agent Harness - 完整的 Agent 框架"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="命令")
    
    # run 命令
    run_parser = subparsers.add_parser("run", help="运行 Agent")
    run_parser.add_argument("--model", "-m", help="模型 ID")
    run_parser.add_argument("--workspace", "-w", help="工作目录")
    
    # test 命令
    test_parser = subparsers.add_parser("test", help="运行测试")
    
    # info 命令
    info_parser = subparsers.add_parser("info", help="显示信息")
    
    args = parser.parse_args()
    
    if args.command == "run":
        from .agent import Agent, AgentConfig
        
        config = AgentConfig()
        if args.model:
            config.model = args.model
        if args.workspace:
            config.workspace = args.workspace
        
        agent = Agent(config)
        agent.run_interactive()
    
    elif args.command == "test":
        # 运行测试
        import subprocess
        test_dir = Path(__file__).parent.parent
        result = subprocess.run(
            [sys.executable, "-m", "pytest", str(test_dir), "-v"],
            cwd=test_dir
        )
        sys.exit(result.returncode)
    
    elif args.command == "info":
        print("OpenAI Agent Harness v1.0.0")
        print(f"Python: {sys.version}")
        print(f"Workspace: {Path.cwd()}")
        
        from .agent import Agent
        agent = Agent()
        print(f"Model: {agent.config.model}")
        print(f"Tools: {list(agent.tools._tools.keys())}")
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()