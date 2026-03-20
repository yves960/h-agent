#!/usr/bin/env python3
"""
h_agent/cli/init_wizard.py - Interactive setup wizard

Provides h-agent init command with guided configuration.
"""

import os
import sys
import getpass
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from h_agent.core.config import (
    AGENT_CONFIG_DIR,
    AGENT_CONFIG_FILE,
    set_config,
    get_config,
    list_config,
    _get_secret,
)


def _print_banner():
    print()
    print("=" * 50)
    print("  h-agent Setup Wizard")
    print("=" * 50)
    print()


def _print_section(title: str):
    print()
    print(f"── {title} ──")


def _ask(prompt: str, default: str = "", password: bool = False) -> str:
    """Ask for input with default value."""
    if default:
        prompt = f"{prompt} [{default}]: "
    else:
        prompt = f"{prompt}: "
    
    if password:
        value = getpass.getpass(prompt)
    else:
        value = input(prompt)
    
    if not value and default:
        return default
    return value


def _ask_choice(prompt: str, options: list, default: int = 0) -> str:
    """Ask for a choice from a list."""
    print(f"\n{prompt}")
    for i, opt in enumerate(options, 1):
        marker = " (default)" if i - 1 == default else ""
        print(f"  {i}. {opt}{marker}")
    
    while True:
        choice = input(f"Enter choice [1-{len(options)}]: ").strip()
        if not choice:
            return options[default]
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(options):
                return options[idx]
        except ValueError:
            pass
        print(f"Please enter a number between 1 and {len(options)}")


def _check_existing_config():
    """Check what configuration already exists."""
    print("Checking existing configuration...")
    
    # Check for API key
    existing_key = _get_secret("OPENAI_API_KEY")
    if existing_key and existing_key != "sk-dummy":
        print(f"  ✓ API key found")
    else:
        print(f"  ✗ API key not configured")
    
    # Check config file
    if AGENT_CONFIG_FILE.exists():
        with open(AGENT_CONFIG_FILE) as f:
            content = f.read()
            if content.strip():
                print(f"  ✓ Config file exists: {AGENT_CONFIG_FILE}")
            else:
                print(f"  ○ Config file is empty")
        print(f"  Config location: {AGENT_CONFIG_DIR}")
    else:
        print(f"  ○ No config file found")
        print(f"  Config will be created at: {AGENT_CONFIG_DIR}")
    
    print()
    return existing_key and existing_key != "sk-dummy"


def _setup_api_key():
    """Setup API key."""
    _print_section("API Key Configuration")
    
    print("""
You need an API key to use h-agent. h-agent supports:
  - OpenAI (api.openai.com)
  - Compatible APIs (DeepSeek, Azure OpenAI, etc.)
""")
    
    # Ask for provider
    provider = _ask_choice(
        "Which API provider do you want to use?",
        ["OpenAI", "Compatible API (DeepSeek, Azure, etc.)"]
    )
    
    if provider == "OpenAI":
        base_url = "https://api.openai.com/v1"
        model = "gpt-4o"
        print(f"\n  Base URL: {base_url}")
        print(f"  Model: {model}")
        
    else:
        base_url = _ask("API Base URL", "https://api.openai.com/v1")
        model = _ask("Model ID", "gpt-4o")
    
    # Ask for API key
    print()
    api_key = _ask("API Key", password=True)
    
    if not api_key:
        print("Error: API key is required")
        return None, None, None
    
    return api_key, base_url, model


def _setup_model(base_url: str, current_model: str = ""):
    """Setup model selection."""
    _print_section("Model Selection")
    
    # Common model presets
    presets = {
        "OpenAI GPT-4o": ("https://api.openai.com/v1", "gpt-4o"),
        "OpenAI GPT-4o-mini": ("https://api.openai.com/v1", "gpt-4o-mini"),
        "OpenAI GPT-4 Turbo": ("https://api.openai.com/v1", "gpt-4-turbo"),
        "DeepSeek V3": ("https://api.deepseek.com/v1", "deepseek-chat"),
        "DeepSeek Coder": ("https://api.deepseek.com/v1", "deepseek-coder"),
        "Custom": ("", ""),
    }
    
    if "deepseek" in base_url.lower():
        default = 3  # DeepSeek V3
    elif "openai" in base_url.lower():
        default = 0  # GPT-4o
    else:
        default = 5  # Custom
    
    choice = _ask_choice(
        "Which model do you want to use?",
        list(presets.keys()),
        default=default
    )
    
    if choice != "Custom":
        url, model = presets[choice]
        return url or base_url, model
    else:
        custom_url = _ask("API Base URL", base_url)
        custom_model = _ask("Model ID", current_model or "gpt-4o")
        return custom_url, custom_model


def _setup_workspace():
    """Setup workspace directory."""
    _print_section("Workspace Configuration")
    
    default_ws = str(Path.home() / ".h-agent" / "workspace")
    workspace = _ask("Workspace directory", default_ws)
    
    if workspace != default_ws:
        create = input(f"Create directory {workspace}? [Y/n]: ").strip().lower()
        if create in ("", "y", "yes"):
            os.makedirs(workspace, exist_ok=True)
    
    return workspace


def _save_config(api_key: str, base_url: str, model: str, workspace: str):
    """Save all configuration."""
    _print_section("Saving Configuration")
    
    # Ensure config directory exists
    AGENT_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    
    # Save API key securely
    set_config("OPENAI_API_KEY", api_key, secure=True)
    print("  ✓ API key saved securely")
    
    # Save other config
    set_config("OPENAI_BASE_URL", base_url, secure=False)
    print(f"  ✓ Base URL: {base_url}")
    
    set_config("MODEL_ID", model, secure=False)
    print(f"  ✓ Model: {model}")
    
    # Create workspace if needed
    if workspace:
        os.makedirs(workspace, exist_ok=True)
        print(f"  ✓ Workspace: {workspace}")
    
    print()


def _create_example_files():
    """Create example files in workspace."""
    _print_section("Creating Example Files")
    
    workspace = Path.home() / ".h-agent" / "workspace"
    workspace.mkdir(parents=True, exist_ok=True)
    
    # Create .env.example
    env_example = workspace / ".env.example"
    with open(env_example, "w") as f:
        f.write("""# h-agent environment configuration
# Copy this file to .env and fill in your values

# OpenAI API Key (required)
OPENAI_API_KEY=your-api-key-here

# API Base URL (optional, defaults to OpenAI)
# OPENAI_BASE_URL=https://api.openai.com/v1

# Model ID (optional, defaults to gpt-4o)
# MODEL_ID=gpt-4o
""")
    print(f"  ✓ Created: {env_example}")
    
    # Create README in workspace
    readme = workspace / "README.md"
    with open(readme, "w") as f:
        f.write("""# h-agent Workspace

This is your h-agent workspace. Your agent will work here.

## Quick Commands

```bash
# Interactive chat
h-agent chat

# Run a single command
h-agent run "帮我写一个快速排序"

# Start daemon
h-agent start

# Check status
h-agent status
```
""")
    print(f"  ✓ Created: {readme}")


def _print_summary():
    """Print setup summary."""
    print()
    print("=" * 50)
    print("  Setup Complete!")
    print("=" * 50)
    print()
    print("Next steps:")
    print("  h-agent chat          # Start interactive chat")
    print("  h-agent run 'hello'   # Run a single command")
    print("  h-agent status        # Check daemon status")
    print()
    print("For more help:")
    print("  h-agent --help")
    print("  cat README.md")
    print()


def run_wizard():
    """Run the interactive setup wizard."""
    _print_banner()
    
    # Check existing config
    has_existing = _check_existing_config()
    
    if has_existing:
        print("Configuration already exists.")
        choice = input("Reconfigure? [y/N]: ").strip().lower()
        if choice not in ("y", "yes"):
            print("Setup cancelled.")
            return 0
    
    # Step 1: API Key
    result = _setup_api_key()
    if result[0] is None:
        print("Setup failed: API key is required.")
        return 1
    
    api_key, base_url, model = result
    
    # Step 2: Model
    base_url, model = _setup_model(base_url, model)
    
    # Step 3: Workspace
    workspace = _setup_workspace()
    
    # Save
    _save_config(api_key, base_url, model, workspace)
    
    # Create example files
    _create_example_files()
    
    # Done
    _print_summary()
    
    return 0


def run_wizard_quick():
    """Quick setup with minimal prompts."""
    _print_banner()
    print("Quick Setup - Minimal Configuration")
    print()
    
    # Check for existing key
    existing_key = _get_secret("OPENAI_API_KEY")
    if existing_key and existing_key != "sk-dummy":
        print(f"API key already configured: {existing_key[:8]}...")
        print()
        return 0
    
    # Need to configure
    api_key = getpass.getpass("Enter your API key: ").strip()
    if not api_key:
        print("Error: API key required")
        return 1
    
    set_config("OPENAI_API_KEY", api_key, secure=True)
    print("API key saved!")
    
    # Create workspace
    workspace = Path.home() / ".h-agent" / "workspace"
    workspace.mkdir(parents=True, exist_ok=True)
    
    print()
    print("Quick setup complete. Run 'h-agent chat' to start!")
    
    return 0


# Run if executed directly
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="h-agent setup wizard")
    parser.add_argument("--quick", action="store_true", help="Quick setup mode")
    args = parser.parse_args()
    
    if args.quick:
        sys.exit(run_wizard_quick())
    else:
        sys.exit(run_wizard())
