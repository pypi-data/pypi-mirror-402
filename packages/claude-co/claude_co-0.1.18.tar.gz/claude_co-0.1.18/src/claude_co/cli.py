"""CLI for Claude-Co setup and configuration."""

import json
import os
import sys
from pathlib import Path


def run_worker(interval: int = 30, persistent: bool = True):
    """Run an autonomous worker that keeps Claude working on tasks."""
    import subprocess
    import time
    import select
    import sys

    initial_prompt = """You are an autonomous worker agent. Your job is to work continuously without stopping.

IMPORTANT: You will receive "CONTINUE WORKING" messages periodically. Each time you receive one:

1. Call check_for_discussions() - respond to any active debates
2. Call check_notifications() - respond to any messages
3. Call get_next_task() - find available work
4. If there's a task: claim it, complete it, call complete_task_v2()
5. If no tasks: just say "No tasks available, waiting..."

DO NOT ask for permission. DO NOT stop working. Stay focused on tasks.

Start by checking for discussions and tasks now."""

    continue_prompt = "CONTINUE WORKING"

    print("Starting autonomous worker mode...")
    print(f"Worker will be prompted every {interval} seconds")
    print(f"Mode: {'Persistent session' if persistent else 'New session each time'}")
    print("Press Ctrl+C to stop\n")

    if not persistent:
        # Original behavior - new session each time
        _run_worker_subprocess(initial_prompt, continue_prompt, interval)
    else:
        # Persistent session - keep Claude running
        _run_worker_persistent(initial_prompt, continue_prompt, interval)


def _run_worker_subprocess(initial_prompt: str, continue_prompt: str, interval: int):
    """Run worker with new subprocess each iteration."""
    import subprocess
    import time

    iteration = 0
    prompt = initial_prompt

    while True:
        iteration += 1
        print(f"\n{'='*50}")
        print(f"Worker iteration {iteration} - {time.strftime('%H:%M:%S')}")
        print('='*50)

        try:
            subprocess.run(
                ["claude", "-p", prompt, "--dangerously-skip-permissions"],
                capture_output=False,
                text=True,
                timeout=300
            )
        except subprocess.TimeoutExpired:
            print("[Worker] Iteration timed out, continuing...")
        except FileNotFoundError:
            print("[Worker] Error: 'claude' command not found.")
            return
        except KeyboardInterrupt:
            print("\n[Worker] Stopped by user")
            return

        prompt = continue_prompt  # Use shorter prompt after first

        print(f"\n[Worker] Sleeping {interval}s...")
        try:
            time.sleep(interval)
        except KeyboardInterrupt:
            print("\n[Worker] Stopped by user")
            return


def _run_worker_persistent(initial_prompt: str, continue_prompt: str, interval: int):
    """Run worker with persistent Claude session."""
    import subprocess
    import time
    import threading
    import sys

    print("[Worker] Starting persistent Claude session...")

    try:
        # Start Claude in interactive mode
        process = subprocess.Popen(
            ["claude", "--dangerously-skip-permissions"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
    except FileNotFoundError:
        print("[Worker] Error: 'claude' command not found.")
        return

    # Thread to print Claude's output
    def print_output():
        try:
            for line in process.stdout:
                print(line, end='', flush=True)
        except:
            pass

    output_thread = threading.Thread(target=print_output, daemon=True)
    output_thread.start()

    # Give Claude a moment to start
    time.sleep(2)

    iteration = 0
    try:
        # Send initial prompt
        print(f"\n[Worker] Sending initial prompt...")
        process.stdin.write(initial_prompt + "\n")
        process.stdin.flush()

        while process.poll() is None:  # While Claude is still running
            time.sleep(interval)
            iteration += 1

            print(f"\n{'='*50}")
            print(f"[Worker] Iteration {iteration} - {time.strftime('%H:%M:%S')}")
            print('='*50 + "\n")

            # Send continue prompt
            try:
                process.stdin.write(continue_prompt + "\n")
                process.stdin.flush()
            except BrokenPipeError:
                print("[Worker] Claude session ended")
                break

    except KeyboardInterrupt:
        print("\n[Worker] Stopping...")
        process.terminate()
        process.wait(timeout=5)
        print("[Worker] Stopped")


def setup_hooks():
    """Install Claude Code hooks for automatic discussion checking.

    Installs to the PROJECT's .claude/settings.json (not global).
    Run this from your project directory.
    """
    # Install to project-level settings, not global
    settings_path = Path.cwd() / ".claude" / "settings.json"

    # Load existing settings or create new
    if settings_path.exists():
        with open(settings_path) as f:
            try:
                settings = json.load(f)
            except json.JSONDecodeError:
                settings = {}
    else:
        settings = {}

    # Ensure hooks section exists
    if "hooks" not in settings:
        settings["hooks"] = {}

    # New hook format for Claude Code (2025+)
    # Format: {"matcher": "", "hooks": [{"type": "command", "command": "..."}]}

    # PreToolUse hook - reminder before tool use
    pre_tool_command = "echo '[Claude-Co] Remember: Check for discussions and messages from other agents.'"

    if "PreToolUse" not in settings["hooks"]:
        settings["hooks"]["PreToolUse"] = []

    # Check if our hook already exists (check both old and new formats)
    def has_claude_co_hook(hooks_list):
        for hook in hooks_list:
            if isinstance(hook, dict):
                # New format: check nested hooks array
                if "hooks" in hook:
                    for h in hook.get("hooks", []):
                        if "Claude-Co" in h.get("command", ""):
                            return True
                # Old format: check command directly
                if "Claude-Co" in hook.get("command", ""):
                    return True
        return False

    if not has_claude_co_hook(settings["hooks"]["PreToolUse"]):
        settings["hooks"]["PreToolUse"].append({
            "matcher": "",  # Match all tool uses (empty string = match all)
            "hooks": [{"type": "command", "command": pre_tool_command}]
        })

    # UserPromptSubmit hook - reminder when user sends a message
    submit_command = "echo '[Claude-Co] IMPORTANT: Call check_for_discussions() and check_notifications() FIRST before doing anything else.'"

    if "UserPromptSubmit" not in settings["hooks"]:
        settings["hooks"]["UserPromptSubmit"] = []

    if not has_claude_co_hook(settings["hooks"]["UserPromptSubmit"]):
        settings["hooks"]["UserPromptSubmit"].append({
            "matcher": "",  # Match all prompts (empty string = match all)
            "hooks": [{"type": "command", "command": submit_command}]
        })

    # Clean up any old-format hooks that might cause errors
    def clean_old_format_hooks(hooks_list):
        cleaned = []
        for hook in hooks_list:
            if isinstance(hook, dict):
                # Skip old format hooks (have "command" at top level, no "hooks" array)
                if "command" in hook and "hooks" not in hook:
                    continue
                cleaned.append(hook)
        return cleaned

    settings["hooks"]["PreToolUse"] = clean_old_format_hooks(settings["hooks"]["PreToolUse"])
    settings["hooks"]["UserPromptSubmit"] = clean_old_format_hooks(settings["hooks"]["UserPromptSubmit"])

    # Write settings
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    with open(settings_path, "w") as f:
        json.dump(settings, f, indent=2)

    print(f"Installed Claude-Co hooks to {settings_path}")
    print("\nHooks added (new format):")
    print("  - PreToolUse: Reminder to check discussions")
    print("  - UserPromptSubmit: Prompt to check discussions first")
    print("\nRestart Claude Code for changes to take effect.")
    return True


def setup_project(url: str = None, api_key: str = None, group: str = None, codebase: str = None, agent_id: str = None):
    """Set up claude-co for the current project directory.

    If .claude-co.json exists, reads connection config from it.
    Otherwise, url/api_key/group are required.

    Creates:
    - .claude-co.json - Connection config (server URL, API key, group)
    - .claude.json - MCP server config (per-project)
    - .claude/settings.json - Hooks (per-project)
    """
    config_path = Path.cwd() / ".claude-co.json"

    # Try to load existing config
    existing_config = {}
    if config_path.exists():
        try:
            with open(config_path) as f:
                existing_config = json.load(f)
            print(f"Found existing config: {config_path}")
        except json.JSONDecodeError:
            pass

    # Use provided args or fall back to existing config
    url = url or existing_config.get("url")
    api_key = api_key or existing_config.get("api_key")
    group = group or existing_config.get("group")
    codebase = codebase or existing_config.get("codebase") or Path.cwd().name

    # Validate required fields
    if not url or not api_key or not group:
        print("Error: Missing required configuration.")
        print("")
        if config_path.exists():
            print(f"Your {config_path} is missing required fields.")
        else:
            print("No .claude-co.json found. Please provide connection details:")
        print("")
        print("Usage: claude-co setup <url> <api_key> <group>")
        print("   or: Create .claude-co.json with url, api_key, group fields")
        sys.exit(1)

    # Get agent ID
    if not agent_id:
        default_id = os.environ.get("USER", "user") + "-claude"
        agent_id = input(f"Enter your agent ID [{default_id}]: ").strip() or default_id

    project_path = str(Path.cwd().absolute())

    # 1. Create/update .claude-co.json (connection config)
    connection_config = {
        "url": url,
        "api_key": api_key,
        "group": group,
        "codebase": codebase,
        "project_path": project_path
    }
    with open(config_path, "w") as f:
        json.dump(connection_config, f, indent=2)

    # 2. Create .claude.json (MCP server config - per-project)
    mcp_config_path = Path.cwd() / ".claude.json"
    if mcp_config_path.exists():
        with open(mcp_config_path) as f:
            try:
                mcp_config = json.load(f)
            except json.JSONDecodeError:
                mcp_config = {}
    else:
        mcp_config = {}

    if "mcpServers" not in mcp_config:
        mcp_config["mcpServers"] = {}

    # Detect venv and use its python, otherwise fallback to generic python
    venv_python = Path.cwd() / ".venv" / "bin" / "python"
    if venv_python.exists():
        python_command = str(venv_python.absolute())
        print(f"  Using venv Python: {python_command}")
    else:
        python_command = "python"
        print("  Using system Python (no .venv found)")

    mcp_config["mcpServers"]["claude-co"] = {
        "command": python_command,
        "args": ["-m", "claude_co", "run"],
        "env": {
            "AGENT_ID": agent_id
        }
    }

    with open(mcp_config_path, "w") as f:
        json.dump(mcp_config, f, indent=2)

    # Also save as "current" project so MCP server can find it
    current_dir = Path.home() / ".claude-co"
    current_dir.mkdir(exist_ok=True)
    with open(current_dir / "current.json", "w") as f:
        json.dump(connection_config, f, indent=2)

    print(f"\nProject configured for claude-co:")
    print(f"  Connection: {config_path}")
    print(f"  MCP Server: {mcp_config_path}")
    print(f"  Server URL: {url}")
    print(f"  Group: {group}")
    print(f"  Codebase: {codebase}")
    print(f"  Agent ID: {agent_id}")

    # 3. Set up hooks for this project
    print("\nSetting up hooks...")
    setup_hooks()

    print("\nDone! Restart Claude Code in this directory.")


def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Claude-Co: Multi-agent coordination for Claude Code"
    )
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # setup command
    setup_parser = subparsers.add_parser(
        "setup",
        help="Configure current project (reads from .claude-co.json if it exists)"
    )
    setup_parser.add_argument("url", nargs="?", help="Server URL (optional if .claude-co.json exists)")
    setup_parser.add_argument("api_key", nargs="?", help="API key (optional if .claude-co.json exists)")
    setup_parser.add_argument("group", nargs="?", help="Group name (optional if .claude-co.json exists)")
    setup_parser.add_argument("--codebase", help="Codebase name (default: directory name)")
    setup_parser.add_argument("--agent-id", help="Your agent ID (default: username-claude)")

    # setup-hooks command
    subparsers.add_parser(
        "setup-hooks",
        help="Install Claude Code hooks for automatic discussion checking"
    )

    # worker command
    worker_parser = subparsers.add_parser(
        "worker",
        help="Start an autonomous worker that continuously processes tasks"
    )
    worker_parser.add_argument(
        "--interval", "-i",
        type=int,
        default=30,
        help="Seconds between worker iterations (default: 30)"
    )
    worker_parser.add_argument(
        "--no-persistent",
        action="store_true",
        help="Start new Claude session each iteration (instead of keeping one alive)"
    )

    # run command (default - runs MCP server)
    subparsers.add_parser(
        "run",
        help="Run the MCP server (used by Claude Code)"
    )

    args = parser.parse_args()

    if args.command == "setup":
        setup_project(args.url, args.api_key, args.group, args.codebase, args.agent_id)
    elif args.command == "setup-hooks":
        setup_hooks()
    elif args.command == "worker":
        run_worker(args.interval, persistent=not args.no_persistent)
    elif args.command == "run":
        # Run MCP server
        from .server import main as run_server
        run_server()
    elif args.command is None:
        # Show welcome message when no command given
        print("""
╔═══════════════════════════════════════════════════════════════╗
║                        Claude-Co                              ║
║         Multi-agent coordination for Claude Code              ║
╚═══════════════════════════════════════════════════════════════╝

Getting started:

  1. Set up a project:
     cd your-project
     claude-co setup <server-url> <api-key> <group>

  2. Start Claude Code in that directory

  3. The agent will have access to coordination tools!

Commands:
  setup        Configure a project for coordination
  setup-hooks  Install reminder hooks (included in setup)
  worker       Run autonomous worker mode
  run          Run MCP server (used internally by Claude Code)

For more info: https://github.com/jude-hawrani/Claude-Co
""")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
