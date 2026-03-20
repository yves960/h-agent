#!/usr/bin/env python3
"""
cross_platform_shell.py - 跨平台 Shell 支持

支持：
- Linux/macOS: bash
- Windows: PowerShell
"""

import os
import sys
import subprocess
import platform
from typing import Tuple


def get_shell_info() -> Tuple[str, list]:
    """
    获取当前系统的 shell 信息。
    
    Returns:
        (shell_name, shell_args)
    """
    system = platform.system().lower()
    
    if system == "windows":
        # Windows: 使用 PowerShell
        return "powershell", ["powershell.exe", "-Command"]
    else:
        # Linux/macOS: 使用 bash
        return "bash", ["/bin/bash", "-c"]


def run_command(command: str, cwd: str = None, timeout: int = 120) -> str:
    """
    跨平台执行命令。
    
    Args:
        command: 要执行的命令
        cwd: 工作目录
        timeout: 超时时间（秒）
    
    Returns:
        命令输出
    """
    shell_name, shell_args = get_shell_info()
    
    # 危险命令检测
    dangerous_patterns = [
        "rm -rf /",
        "sudo rm",
        "mkfs",
        "dd if=",
        "> /dev/sd",
        "del /s /q",  # Windows
        "format c:",  # Windows
    ]
    
    if any(d in command.lower() for d in dangerous_patterns):
        return "Error: Dangerous command blocked"
    
    try:
        if platform.system().lower() == "windows":
            # Windows PowerShell
            result = subprocess.run(
                shell_args + [command],
                cwd=cwd or os.getcwd(),
                capture_output=True,
                text=True,
                timeout=timeout,
            )
        else:
            # Linux/macOS bash
            result = subprocess.run(
                command,
                shell=True,
                cwd=cwd or os.getcwd(),
                capture_output=True,
                text=True,
                timeout=timeout,
            )
        
        output = (result.stdout + result.stderr).strip()
        return output[:50000] if output else "(no output)"
    
    except subprocess.TimeoutExpired:
        return f"Error: Timeout ({timeout}s)"
    except FileNotFoundError as e:
        return f"Error: Command not found: {e}"
    except Exception as e:
        return f"Error: {e}"


def normalize_path(path: str) -> str:
    """
    规范化路径（跨平台）。
    
    Args:
        path: 输入路径
    
    Returns:
        规范化后的路径
    """
    # 替换路径分隔符
    if platform.system().lower() == "windows":
        path = path.replace("/", "\\")
    else:
        path = path.replace("\\", "/")
    
    return os.path.normpath(path)


def get_platform_info() -> dict:
    """
    获取平台信息。
    
    Returns:
        平台信息字典
    """
    return {
        "system": platform.system(),
        "release": platform.release(),
        "machine": platform.machine(),
        "python": platform.python_version(),
        "shell": get_shell_info()[0],
    }


# ============================================================
# 跨平台命令适配器
# ============================================================

class CrossPlatformCommands:
    """跨平台命令适配器。"""
    
    @staticmethod
    def list_dir(path: str = ".") -> str:
        """列出目录内容。"""
        if platform.system().lower() == "windows":
            return run_command(f"Get-ChildItem -Name '{path}'")
        else:
            return run_command(f"ls -la '{path}'")
    
    @staticmethod
    def change_dir(path: str) -> str:
        """切换目录。"""
        if platform.system().lower() == "windows":
            return run_command(f"Set-Location '{path}'; Get-Location")
        else:
            return run_command(f"cd '{path}' && pwd")
    
    @staticmethod
    def copy_file(src: str, dst: str) -> str:
        """复制文件。"""
        if platform.system().lower() == "windows":
            return run_command(f"Copy-Item '{src}' '{dst}'")
        else:
            return run_command(f"cp '{src}' '{dst}'")
    
    @staticmethod
    def move_file(src: str, dst: str) -> str:
        """移动文件。"""
        if platform.system().lower() == "windows":
            return run_command(f"Move-Item '{src}' '{dst}'")
        else:
            return run_command(f"mv '{src}' '{dst}'")
    
    @staticmethod
    def delete_file(path: str) -> str:
        """删除文件。"""
        # 安全检查
        if path in ["/", "C:\\", "C:"]:
            return "Error: Cannot delete root directory"
        
        if platform.system().lower() == "windows":
            return run_command(f"Remove-Item '{path}' -Force")
        else:
            return run_command(f"rm -f '{path}'")
    
    @staticmethod
    def create_dir(path: str) -> str:
        """创建目录。"""
        if platform.system().lower() == "windows":
            return run_command(f"New-Item -ItemType Directory -Path '{path}' -Force")
        else:
            return run_command(f"mkdir -p '{path}'")
    
    @staticmethod
    def find_files(pattern: str, path: str = ".") -> str:
        """查找文件。"""
        if platform.system().lower() == "windows":
            return run_command(f"Get-ChildItem -Path '{path}' -Recurse -Filter '{pattern}' | Select-Object FullName")
        else:
            return run_command(f"find '{path}' -name '{pattern}'")
    
    @staticmethod
    def grep(pattern: str, path: str, recursive: bool = True) -> str:
        """搜索文本。"""
        if platform.system().lower() == "windows":
            recurse = "-Recurse" if recursive else ""
            return run_command(f"Get-ChildItem {recurse} '{path}' | Select-String '{pattern}'")
        else:
            r = "-r" if recursive else ""
            return run_command(f"grep {r} '{pattern}' '{path}'")
    
    @staticmethod
    def env_vars() -> str:
        """获取环境变量。"""
        if platform.system().lower() == "windows":
            return run_command("Get-ChildItem Env: | Format-Table -AutoSize")
        else:
            return run_command("env")


# ============================================================
# 测试
# ============================================================

def main():
    print(f"\033[36m跨平台 Shell 测试\033[0m")
    print("=" * 50)
    
    # 显示平台信息
    info = get_platform_info()
    print(f"系统: {info['system']} {info['release']}")
    print(f"架构: {info['machine']}")
    print(f"Shell: {info['shell']}")
    print(f"Python: {info['python']}")
    
    # 测试命令
    print("\n=== 命令测试 ===")
    
    # 列出当前目录
    print("\n列出当前目录:")
    result = CrossPlatformCommands.list_dir(".")
    print(result[:500])
    
    # 查找 Python 文件
    print("\n查找 Python 文件:")
    result = CrossPlatformCommands.find_files("*.py", ".")
    print(result[:500])
    
    print("\n✅ 跨平台 Shell 测试通过")


if __name__ == "__main__":
    main()