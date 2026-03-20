#!/usr/bin/env python3
"""
c06_intelligence.py - Intelligence (OpenAI Version)

赋予灵魂，教会记忆。
系统提示词的分层构建: Identity / Soul / Tools / Skills / Memory / Bootstrap

8层组装:
  1. Identity  - 我是谁
  2. Soul      - 性格、价值观
  3. Tools     - 可用工具
  4. Skills    - 技能文件
  5. Memory    - 记忆/上下文
  6. User      - 用户信息
  7. Bootstrap - 启动指令
  8. Runtime   - 运行时状态
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, field

from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY", "sk-dummy"),
    base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
)
MODEL = os.getenv("MODEL_ID", "gpt-4o")

WORKSPACE_DIR = Path.cwd() / ".agent_workspace"
WORKSPACE_DIR.mkdir(parents=True, exist_ok=True)

# Bootstrap 文件
BOOTSTRAP_FILES = ["SOUL.md", "IDENTITY.md", "TOOLS.md", "USER.md", "AGENTS.md", "MEMORY.md"]

MAX_FILE_CHARS = 20000
MAX_TOTAL_CHARS = 150000


# ============================================================
# Bootstrap Loader
# ============================================================

class BootstrapLoader:
    """加载 Bootstrap 文件。"""
    
    def __init__(self, agent_dir: Path = None):
        self.agent_dir = agent_dir or WORKSPACE_DIR
    
    def load_file(self, filename: str) -> str:
        """加载单个文件。"""
        path = self.agent_dir / filename
        if path.exists():
            content = path.read_text(encoding="utf-8")
            return content[:MAX_FILE_CHARS]
        return ""
    
    def load_all(self) -> Dict[str, str]:
        """加载所有 Bootstrap 文件。"""
        result = {}
        for filename in BOOTSTRAP_FILES:
            content = self.load_file(filename)
            if content:
                result[filename] = content
        return result


# ============================================================
# Skills Manager
# ============================================================

class SkillsManager:
    """管理技能文件。"""
    
    def __init__(self, skills_dir: Path = None):
        self.skills_dir = skills_dir or WORKSPACE_DIR / "skills"
        self.skills_dir.mkdir(parents=True, exist_ok=True)
    
    def list_skills(self) -> List[str]:
        """列出所有技能。"""
        skills = []
        for skill_dir in self.skills_dir.iterdir():
            if skill_dir.is_dir() and (skill_dir / "SKILL.md").exists():
                skills.append(skill_dir.name)
        return skills
    
    def load_skill(self, skill_name: str) -> str:
        """加载技能内容。"""
        skill_file = self.skills_dir / skill_name / "SKILL.md"
        if skill_file.exists():
            return skill_file.read_text(encoding="utf-8")[:MAX_FILE_CHARS]
        return ""
    
    def discover_skills(self, query: str = "") -> List[str]:
        """发现相关技能。"""
        # 简单实现：返回所有技能
        return self.list_skills()


# ============================================================
# Memory Store
# ============================================================

class MemoryStore:
    """记忆存储。"""
    
    def __init__(self, memory_dir: Path = None):
        self.memory_dir = memory_dir or WORKSPACE_DIR / "memory"
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        self._memory: Dict[str, str] = {}
        self._load()
    
    def _load(self):
        """加载记忆文件。"""
        for mem_file in self.memory_dir.glob("*.md"):
            key = mem_file.stem
            self._memory[key] = mem_file.read_text(encoding="utf-8")
    
    def get(self, key: str) -> str:
        """获取记忆。"""
        return self._memory.get(key, "")
    
    def set(self, key: str, value: str):
        """设置记忆。"""
        self._memory[key] = value
        mem_file = self.memory_dir / f"{key}.md"
        mem_file.write_text(value, encoding="utf-8")
    
    def search(self, query: str) -> List[str]:
        """搜索记忆。"""
        results = []
        query_lower = query.lower()
        for key, content in self._memory.items():
            if query_lower in content.lower() or query_lower in key.lower():
                results.append(f"[{key}]\n{content[:500]}")
        return results
    
    def format_for_prompt(self) -> str:
        """格式化为提示词。"""
        if not self._memory:
            return ""
        
        lines = ["# Memory\n"]
        for key, content in self._memory.items():
            lines.append(f"## {key}\n{content}\n")
        return "\n".join(lines)


# ============================================================
# Prompt Builder
# ============================================================

class PromptBuilder:
    """构建分层系统提示词。"""
    
    def __init__(self, agent_id: str = "default"):
        self.agent_id = agent_id
        self.bootstrap = BootstrapLoader()
        self.skills = SkillsManager()
        self.memory = MemoryStore()
    
    def build(self, runtime_context: dict = None) -> str:
        """构建完整的系统提示词。"""
        layers = []
        total_chars = 0
        
        # Layer 1: Identity
        identity = self.bootstrap.load_file("IDENTITY.md")
        if identity:
            layers.append(f"# Identity\n{identity}")
            total_chars += len(identity)
        
        # Layer 2: Soul
        soul = self.bootstrap.load_file("SOUL.md")
        if soul:
            layers.append(f"# Soul\n{soul}")
            total_chars += len(soul)
        
        # Layer 3: Tools
        tools = self.bootstrap.load_file("TOOLS.md")
        if tools:
            layers.append(f"# Tools\n{tools}")
            total_chars += len(tools)
        
        # Layer 4: Skills
        skill_list = self.skills.list_skills()
        if skill_list:
            skill_content = f"# Available Skills\n{', '.join(skill_list)}"
            layers.append(skill_content)
            total_chars += len(skill_content)
        
        # Layer 5: Memory
        memory_content = self.memory.format_for_prompt()
        if memory_content:
            layers.append(memory_content)
            total_chars += len(memory_content)
        
        # Layer 6: User
        user = self.bootstrap.load_file("USER.md")
        if user:
            layers.append(f"# User\n{user}")
            total_chars += len(user)
        
        # Layer 7: Bootstrap
        bootstrap = self.bootstrap.load_file("BOOTSTRAP.md")
        if bootstrap:
            layers.append(f"# Instructions\n{bootstrap}")
            total_chars += len(bootstrap)
        
        # Layer 8: Runtime
        if runtime_context:
            runtime = json.dumps(runtime_context, indent=2)
            layers.append(f"# Runtime Context\n```\n{runtime}\n```")
        
        # 检查总长度
        result = "\n\n".join(layers)
        if len(result) > MAX_TOTAL_CHARS:
            result = result[:MAX_TOTAL_CHARS] + "\n\n[Truncated due to length]"
        
        return result


# ============================================================
# Intelligent Agent
# ============================================================

class IntelligentAgent:
    """智能 Agent。"""
    
    def __init__(self, agent_id: str = "default"):
        self.agent_id = agent_id
        self.prompt_builder = PromptBuilder(agent_id)
        self.messages: List[dict] = []
    
    def chat(self, user_input: str) -> str:
        """对话。"""
        system_prompt = self.prompt_builder.build({
            "agent_id": self.agent_id,
            "cwd": str(Path.cwd()),
        })
        
        self.messages.append({"role": "user", "content": user_input})
        
        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=[{"role": "system", "content": system_prompt}] + self.messages[-20:],
                max_tokens=4096,
            )
            reply = response.choices[0].message.content
            self.messages.append({"role": "assistant", "content": reply})
            return reply
        except Exception as e:
            return f"Error: {e}"
    
    def remember(self, key: str, value: str):
        """记住。"""
        self.prompt_builder.memory.set(key, value)
    
    def recall(self, query: str) -> List[str]:
        """回忆。"""
        return self.prompt_builder.memory.search(query)
    
    def load_skill(self, skill_name: str) -> str:
        """加载技能。"""
        return self.prompt_builder.skills.load_skill(skill_name)


# ============================================================
# Main
# ============================================================

def main():
    print(f"\033[36mOpenAI Agent Harness - c06 (Intelligence)\033[0m")
    print(f"Model: {MODEL}")
    
    agent = IntelligentAgent("test")
    
    # 测试记忆
    agent.remember("project", "OpenAI Agent Harness - a learning project")
    print("记住: project")
    
    # 测试回忆
    results = agent.recall("project")
    print(f"回忆 'project': {results}")
    
    # 测试提示词构建
    prompt = agent.prompt_builder.build({"test": True})
    print(f"\n系统提示词长度: {len(prompt)} chars")
    
    print("\n✅ c06 测试通过")


if __name__ == "__main__":
    main()