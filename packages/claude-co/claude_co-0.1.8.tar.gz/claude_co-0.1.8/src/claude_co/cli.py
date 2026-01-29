"""CLI for Claude-Co setup and configuration."""

import json
import os
import sys
from pathlib import Path


def get_claude_config_path() -> Path:
    """Find Claude Code's config file."""
    # Check common locations
    candidates = [
        Path.home() / ".claude.json",
        Path.home() / ".config" / "claude" / "settings.json",
        Path.home() / ".claude" / "settings.json",
    ]

    for path in candidates:
        if path.exists():
            return path

    # Default to ~/.claude.json
    return Path.home() / ".claude.json"


def install_mcp_server(agent_id: str = None):
    """Add claude-co to Claude Code's MCP config."""
    config_path = get_claude_config_path()

    # Load existing config or create new
    if config_path.exists():
        with open(config_path) as f:
            try:
                config = json.load(f)
            except json.JSONDecodeError:
                config = {}
    else:
        config = {}

    # Ensure mcpServers exists
    if "mcpServers" not in config:
        config["mcpServers"] = {}

    # Check if already installed
    if "claude-co" in config["mcpServers"]:
        print(f"claude-co is already configured in {config_path}")
        existing = config["mcpServers"]["claude-co"]
        if "env" in existing and "AGENT_ID" in existing["env"]:
            print(f"  AGENT_ID: {existing['env']['AGENT_ID']}")
        return True

    # Get agent ID
    if not agent_id:
        # Try to get username
        default_id = os.environ.get("USER", "user") + "-claude"
        agent_id = input(f"Enter your agent ID [{default_id}]: ").strip() or default_id

    # Add claude-co MCP server
    config["mcpServers"]["claude-co"] = {
        "command": "python",
        "args": ["-m", "claude_co"],
        "env": {
            "AGENT_ID": agent_id
        }
    }

    # Backup existing config
    if config_path.exists():
        backup_path = config_path.with_suffix(".json.backup")
        config_path.rename(backup_path)
        print(f"Backed up existing config to {backup_path}")

    # Write new config
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)

    print(f"\nInstalled claude-co MCP server to {config_path}")
    print(f"  AGENT_ID: {agent_id}")

    # Also install hooks
    print("\nInstalling Claude Code hooks...")
    setup_hooks()

    return True


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
    """Install Claude Code hooks for automatic discussion checking."""
    # Find Claude settings file
    settings_paths = [
        Path.home() / ".claude" / "settings.json",
        Path.home() / ".config" / "claude" / "settings.json",
    ]

    settings_path = None
    for path in settings_paths:
        if path.exists():
            settings_path = path
            break

    # Default to ~/.claude/settings.json
    if not settings_path:
        settings_path = Path.home() / ".claude" / "settings.json"

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

    # Add the pre-tool-use hook reminder
    # This hook runs before every user message and reminds the agent to check discussions
    hook_command = "echo '[Claude-Co] Remember: Check for discussions and messages from other agents before responding.'"

    if "PreToolUse" not in settings["hooks"]:
        settings["hooks"]["PreToolUse"] = []

    # Check if hook already exists
    existing_hooks = settings["hooks"]["PreToolUse"]
    hook_exists = any(
        hook.get("command") == hook_command or
        "Claude-Co" in hook.get("command", "")
        for hook in existing_hooks if isinstance(hook, dict)
    )

    if not hook_exists:
        settings["hooks"]["PreToolUse"].append({
            "matcher": "",  # Match all tool uses
            "command": hook_command
        })

    # Also add a UserPromptSubmit hook
    if "UserPromptSubmit" not in settings["hooks"]:
        settings["hooks"]["UserPromptSubmit"] = []

    submit_hook = "echo '[Claude-Co] IMPORTANT: Call check_for_discussions() and check_notifications() FIRST before doing anything else.'"

    submit_exists = any(
        hook.get("command") == submit_hook or
        "check_for_discussions" in hook.get("command", "")
        for hook in settings["hooks"]["UserPromptSubmit"] if isinstance(hook, dict)
    )

    if not submit_exists:
        settings["hooks"]["UserPromptSubmit"].append({
            "matcher": "",
            "command": submit_hook
        })

    # Write settings
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    with open(settings_path, "w") as f:
        json.dump(settings, f, indent=2)

    print(f"Installed Claude-Co hooks to {settings_path}")
    print("\nHooks added:")
    print("  - PreToolUse: Reminder to check discussions")
    print("  - UserPromptSubmit: Prompt to check discussions first")
    print("\nRestart Claude Code for changes to take effect.")
    return True


def setup_project(url: str, api_key: str, group: str, codebase: str = None):
    """Create .claude-co.json in current directory."""
    if not codebase:
        codebase = Path.cwd().name

    project_path = str(Path.cwd().absolute())
    config = {
        "url": url,
        "api_key": api_key,
        "group": group,
        "codebase": codebase,
        "project_path": project_path
    }

    # Save to project directory
    config_path = Path.cwd() / ".claude-co.json"
    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)

    # Also save as "current" project so MCP server can find it
    current_dir = Path.home() / ".claude-co"
    current_dir.mkdir(exist_ok=True)
    with open(current_dir / "current.json", "w") as f:
        json.dump(config, f, indent=2)

    print(f"Created {config_path}")
    print(f"  Server: {url}")
    print(f"  Group: {group}")
    print(f"  Codebase: {codebase}")
    print(f"  Project path: {project_path}")


def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Claude-Co: Multi-agent coordination for Claude Code"
    )
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # install command
    install_parser = subparsers.add_parser(
        "install",
        help="Add claude-co to Claude Code's MCP config"
    )
    install_parser.add_argument(
        "--agent-id",
        help="Your agent ID (default: username-claude)"
    )

    # setup command
    setup_parser = subparsers.add_parser(
        "setup",
        help="Configure current project to use a coordination server"
    )
    setup_parser.add_argument("url", help="Server URL")
    setup_parser.add_argument("api_key", help="API key")
    setup_parser.add_argument("group", help="Group name")
    setup_parser.add_argument("--codebase", help="Codebase name (default: directory name)")

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

    if args.command == "install":
        install_mcp_server(args.agent_id)
    elif args.command == "setup":
        setup_project(args.url, args.api_key, args.group, args.codebase)
    elif args.command == "setup-hooks":
        setup_hooks()
    elif args.command == "worker":
        run_worker(args.interval, persistent=not args.no_persistent)
    elif args.command == "run" or args.command is None:
        # Run MCP server
        from .server import main as run_server
        run_server()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
