"""
h_agent/core/config.py - Configuration module

Central configuration for the h_agent system.
Loads from environment variables with sensible defaults.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file
load_dotenv(override=True)

# ============================================================
# OpenAI Configuration
# ============================================================

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "sk-dummy")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
MODEL_ID = os.getenv("MODEL_ID", "gpt-4o")

# ============================================================
# Workspace Configuration
# ============================================================

WORKSPACE_DIR = Path.cwd() / ".agent_workspace"
WORKSPACE_DIR.mkdir(parents=True, exist_ok=True)

# ============================================================
# Context Limits
# ============================================================

CONTEXT_SAFE_LIMIT = 180000  # tokens
MAX_TOOL_OUTPUT = 50000

# ============================================================
# Skills Directory
# ============================================================

SKILLS_DIR = Path(__file__).parent.parent / "skills"

# ============================================================
# Session Configuration
# ============================================================

SESSION_DIR = WORKSPACE_DIR / "sessions"
