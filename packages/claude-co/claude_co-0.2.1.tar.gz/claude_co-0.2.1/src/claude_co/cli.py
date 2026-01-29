"""CLI for claude-co setup and configuration."""

import json
import os
import sys
from pathlib import Path

# Supported agent configurations
SUPPORTED_AGENTS = {
    "claude": {
        "name": "Claude Code",
        "cli_command": "claude",
        "cli_args": ["--dangerously-skip-permissions"],
        "prompt_flag": "-p",
        "config_path": Path.home() / ".claude.json",
        "id_suffix": "claude",
        "supports_hooks": True,
    },
    "codex": {
        "name": "OpenAI Codex",
        "cli_command": "codex",
        "cli_args": [],  # Codex uses config file for permissions
        "prompt_flag": "-p",
        "config_path": Path.home() / ".codex" / "config.toml",
        "id_suffix": "codex",
        "supports_hooks": False,  # Codex has different notification system
    },
    "other": {
        "name": "Other Agent",
        "cli_command": None,
        "cli_args": [],
        "prompt_flag": None,
        "config_path": None,
        "id_suffix": "agent",
        "supports_hooks": False,
    }
}


def ask_agent_type() -> str:
    """Prompt user to select their agent type."""
    print("\nWhich AI agent are you using?")
    print("  1) Claude Code (Anthropic)")
    print("  2) OpenAI Codex")
    print("  3) Other / Manual setup")
    print("")

    while True:
        choice = input("Enter choice [1-3]: ").strip()
        if choice == "1":
            return "claude"
        elif choice == "2":
            return "codex"
        elif choice == "3":
            return "other"
        else:
            print("Please enter 1, 2, or 3")


def get_python_command() -> str:
    """Detect venv and return appropriate python command."""
    venv_python = Path.cwd() / ".venv" / "bin" / "python"
    if venv_python.exists():
        return str(venv_python.absolute())
    return "python"


def setup_claude_config(project_path: str, agent_id: str) -> Path:
    """
    Configure MCP server for Claude Code.

    Writes to ~/.claude.json under projects -> <path> -> mcpServers
    """
    config_path = SUPPORTED_AGENTS["claude"]["config_path"]

    if config_path.exists():
        with open(config_path) as f:
            try:
                config = json.load(f)
            except json.JSONDecodeError:
                config = {}
    else:
        config = {}

    # Ensure projects section exists
    if "projects" not in config:
        config["projects"] = {}

    if project_path not in config["projects"]:
        config["projects"][project_path] = {}

    if "mcpServers" not in config["projects"][project_path]:
        config["projects"][project_path]["mcpServers"] = {}

    python_cmd = get_python_command()

    # Add/update claude-co MCP server
    config["projects"][project_path]["mcpServers"]["claude-co"] = {
        "type": "stdio",
        "command": python_cmd,
        "args": ["-m", "claude_co", "run"],
        "env": {
            "AGENT_ID": agent_id
        }
    }

    config_path.parent.mkdir(parents=True, exist_ok=True)
    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)

    return config_path


def setup_codex_config(project_path: str, agent_id: str) -> Path:
    """
    Configure MCP server for OpenAI Codex.

    Writes to ~/.codex/config.toml under [mcp_servers.claude-co]
    """
    config_path = SUPPORTED_AGENTS["codex"]["config_path"]
    config_path.parent.mkdir(parents=True, exist_ok=True)

    python_cmd = get_python_command()

    # Read existing config or create new
    existing_content = ""
    if config_path.exists():
        with open(config_path) as f:
            existing_content = f.read()

    # Check if claude-co section already exists
    if "[mcp_servers.claude-co]" in existing_content:
        # Replace existing section
        import re
        pattern = r'\[mcp_servers\.claude-co\][^\[]*'
        new_section = f'''[mcp_servers.claude-co]
command = "{python_cmd}"
args = ["-m", "claude_co", "run"]
env = {{ AGENT_ID = "{agent_id}" }}

'''
        existing_content = re.sub(pattern, new_section, existing_content)
    else:
        # Append new section
        new_section = f'''
[mcp_servers.claude-co]
command = "{python_cmd}"
args = ["-m", "claude_co", "run"]
env = {{ AGENT_ID = "{agent_id}" }}
'''
        existing_content += new_section

    with open(config_path, "w") as f:
        f.write(existing_content)

    return config_path


def run_worker(interval: int = 30, persistent: bool = True, agent_type: str = None):
    """Run an autonomous worker that keeps the agent working on tasks."""
    import subprocess
    import time

    # Determine agent type from config or parameter
    if not agent_type:
        config_path = Path.cwd() / ".claude-co.json"
        if config_path.exists():
            with open(config_path) as f:
                config = json.load(f)
                agent_type = config.get("agent_type", "claude")
        else:
            agent_type = "claude"  # Default fallback

    agent_config = SUPPORTED_AGENTS.get(agent_type, SUPPORTED_AGENTS["other"])

    if not agent_config["cli_command"]:
        print(f"Error: Worker mode is not supported for '{agent_type}' agent type.")
        print("Worker mode requires a CLI command to invoke the agent.")
        return

    cli_command = agent_config["cli_command"]
    cli_args = agent_config["cli_args"]
    prompt_flag = agent_config["prompt_flag"]

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

    print(f"Starting autonomous worker mode with {agent_config['name']}...")
    print(f"Worker will be prompted every {interval} seconds")
    print(f"Mode: {'Persistent session' if persistent else 'New session each time'}")
    print("Press Ctrl+C to stop\n")

    if not persistent:
        _run_worker_subprocess(initial_prompt, continue_prompt, interval,
                               cli_command, cli_args, prompt_flag)
    else:
        _run_worker_persistent(initial_prompt, continue_prompt, interval,
                               cli_command, cli_args)


def _run_worker_subprocess(initial_prompt: str, continue_prompt: str, interval: int,
                           cli_command: str, cli_args: list, prompt_flag: str):
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
            cmd = [cli_command]
            if prompt_flag:
                cmd.extend([prompt_flag, prompt])
            cmd.extend(cli_args)

            subprocess.run(
                cmd,
                capture_output=False,
                text=True,
                timeout=300
            )
        except subprocess.TimeoutExpired:
            print("[Worker] Iteration timed out, continuing...")
        except FileNotFoundError:
            print(f"[Worker] Error: '{cli_command}' command not found.")
            return
        except KeyboardInterrupt:
            print("\n[Worker] Stopped by user")
            return

        prompt = continue_prompt

        print(f"\n[Worker] Sleeping {interval}s...")
        try:
            time.sleep(interval)
        except KeyboardInterrupt:
            print("\n[Worker] Stopped by user")
            return


def _run_worker_persistent(initial_prompt: str, continue_prompt: str, interval: int,
                           cli_command: str, cli_args: list):
    """Run worker with persistent agent session."""
    import subprocess
    import time
    import threading

    print(f"[Worker] Starting persistent {cli_command} session...")

    try:
        cmd = [cli_command] + cli_args
        process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
    except FileNotFoundError:
        print(f"[Worker] Error: '{cli_command}' command not found.")
        return

    def print_output():
        try:
            for line in process.stdout:
                print(line, end='', flush=True)
        except:
            pass

    output_thread = threading.Thread(target=print_output, daemon=True)
    output_thread.start()

    time.sleep(2)

    iteration = 0
    try:
        print(f"\n[Worker] Sending initial prompt...")
        process.stdin.write(initial_prompt + "\n")
        process.stdin.flush()

        while process.poll() is None:
            time.sleep(interval)
            iteration += 1

            print(f"\n{'='*50}")
            print(f"[Worker] Iteration {iteration} - {time.strftime('%H:%M:%S')}")
            print('='*50 + "\n")

            try:
                process.stdin.write(continue_prompt + "\n")
                process.stdin.flush()
            except BrokenPipeError:
                print("[Worker] Agent session ended")
                break

    except KeyboardInterrupt:
        print("\n[Worker] Stopping...")
        process.terminate()
        process.wait(timeout=5)
        print("[Worker] Stopped")


def setup_hooks():
    """
    Install Claude Code hooks for automatic discussion checking.

    Note: This only works with Claude Code. Other agents have different
    notification systems that should be configured separately.

    Installs to the PROJECT's .claude/settings.json (not global).
    Run this from your project directory.
    """
    settings_path = Path.cwd() / ".claude" / "settings.json"

    if settings_path.exists():
        with open(settings_path) as f:
            try:
                settings = json.load(f)
            except json.JSONDecodeError:
                settings = {}
    else:
        settings = {}

    if "hooks" not in settings:
        settings["hooks"] = {}

    pre_tool_command = "echo '[claude-co] Remember: Check for discussions and messages from other agents.'"

    if "PreToolUse" not in settings["hooks"]:
        settings["hooks"]["PreToolUse"] = []

    def has_claude_co_hook(hooks_list):
        for hook in hooks_list:
            if isinstance(hook, dict):
                if "hooks" in hook:
                    for h in hook.get("hooks", []):
                        if "claude-co" in h.get("command", ""):
                            return True
                if "claude-co" in hook.get("command", ""):
                    return True
        return False

    if not has_claude_co_hook(settings["hooks"]["PreToolUse"]):
        settings["hooks"]["PreToolUse"].append({
            "matcher": "",
            "hooks": [{"type": "command", "command": pre_tool_command}]
        })

    submit_command = "echo '[claude-co] IMPORTANT: Call check_for_discussions() and check_notifications() FIRST before doing anything else.'"

    if "UserPromptSubmit" not in settings["hooks"]:
        settings["hooks"]["UserPromptSubmit"] = []

    if not has_claude_co_hook(settings["hooks"]["UserPromptSubmit"]):
        settings["hooks"]["UserPromptSubmit"].append({
            "matcher": "",
            "hooks": [{"type": "command", "command": submit_command}]
        })

    def clean_old_format_hooks(hooks_list):
        cleaned = []
        for hook in hooks_list:
            if isinstance(hook, dict):
                if "command" in hook and "hooks" not in hook:
                    continue
                cleaned.append(hook)
        return cleaned

    settings["hooks"]["PreToolUse"] = clean_old_format_hooks(settings["hooks"]["PreToolUse"])
    settings["hooks"]["UserPromptSubmit"] = clean_old_format_hooks(settings["hooks"]["UserPromptSubmit"])

    settings_path.parent.mkdir(parents=True, exist_ok=True)
    with open(settings_path, "w") as f:
        json.dump(settings, f, indent=2)

    print(f"  Installed hooks to {settings_path}")
    return True


def setup_project(url: str = None, api_key: str = None, group: str = None,
                  codebase: str = None, agent_id: str = None, agent_type: str = None):
    """
    Set up claude-co for the current project directory.

    If .claude-co.json exists, reads connection config from it.
    Otherwise, url/api_key/group are required.

    Creates/updates:
    - .claude-co.json - Connection config (server URL, API key, group, agent type)
    - Agent-specific MCP config (Claude: ~/.claude.json, Codex: ~/.codex/config.toml)
    - Hooks (Claude Code only)
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
    agent_type = agent_type or existing_config.get("agent_type")

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

    # Ask which agent they're using (if not already set)
    if not agent_type:
        agent_type = ask_agent_type()

    agent_config = SUPPORTED_AGENTS.get(agent_type, SUPPORTED_AGENTS["other"])

    # Get agent ID
    if not agent_id:
        default_suffix = agent_config["id_suffix"]
        default_id = os.environ.get("USER", "user") + "-" + default_suffix
        agent_id = input(f"Enter your agent ID [{default_id}]: ").strip() or default_id

    project_path = str(Path.cwd().absolute())

    # 1. Create/update .claude-co.json
    connection_config = {
        "url": url,
        "api_key": api_key,
        "group": group,
        "codebase": codebase,
        "agent_type": agent_type,
        "project_path": project_path
    }
    with open(config_path, "w") as f:
        json.dump(connection_config, f, indent=2)

    # Also save as "current" project
    current_dir = Path.home() / ".claude-co"
    current_dir.mkdir(exist_ok=True)
    with open(current_dir / "current.json", "w") as f:
        json.dump(connection_config, f, indent=2)

    print(f"\nProject configured:")
    print(f"  Config: {config_path}")
    print(f"  Server URL: {url}")
    print(f"  Group: {group}")
    print(f"  Codebase: {codebase}")
    print(f"  Agent Type: {agent_config['name']}")
    print(f"  Agent ID: {agent_id}")

    # 2. Configure agent-specific MCP server
    python_cmd = get_python_command()
    print(f"\n  Python: {python_cmd}")

    if agent_type == "claude":
        mcp_config_path = setup_claude_config(project_path, agent_id)
        print(f"  MCP Config: {mcp_config_path}")

        # 3. Set up hooks (Claude only)
        print("\nSetting up hooks...")
        setup_hooks()

        print(f"\nDone! Restart Claude Code in this directory.")

    elif agent_type == "codex":
        mcp_config_path = setup_codex_config(project_path, agent_id)
        print(f"  MCP Config: {mcp_config_path}")
        print("\nDone! Restart Codex in this directory.")

    else:
        print("\nManual MCP configuration required.")
        print("Add the following MCP server to your agent's configuration:")
        print(f"""
  Command: {python_cmd}
  Args: ["-m", "claude_co", "run"]
  Environment: AGENT_ID={agent_id}
""")
        print("Done!")


def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="claude-co: Multi-agent coordination for AI coding assistants"
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
    setup_parser.add_argument("--agent-id", help="Your agent ID (default: username-{agent})")
    setup_parser.add_argument("--agent-type", choices=["claude", "codex", "other"],
                              help="Agent type (will prompt if not specified)")

    # setup-hooks command (Claude only)
    subparsers.add_parser(
        "setup-hooks",
        help="Install Claude Code hooks for automatic discussion checking (Claude only)"
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
        help="Start new agent session each iteration (instead of keeping one alive)"
    )
    worker_parser.add_argument(
        "--agent-type",
        choices=["claude", "codex"],
        help="Agent type (default: from .claude-co.json or 'claude')"
    )

    # run command
    subparsers.add_parser(
        "run",
        help="Run the MCP server (used internally by agents)"
    )

    args = parser.parse_args()

    if args.command == "setup":
        setup_project(args.url, args.api_key, args.group, args.codebase,
                      args.agent_id, args.agent_type)
    elif args.command == "setup-hooks":
        print("Installing Claude Code hooks...")
        setup_hooks()
        print("\nRestart Claude Code for changes to take effect.")
    elif args.command == "worker":
        run_worker(args.interval, persistent=not args.no_persistent,
                   agent_type=args.agent_type)
    elif args.command == "run":
        from .server import main as run_server
        run_server()
    elif args.command is None:
        print("""
╔═══════════════════════════════════════════════════════════════╗
║                        claude-co                              ║
║       Multi-agent coordination for AI coding assistants       ║
╚═══════════════════════════════════════════════════════════════╝

Supported Agents:
  - Claude Code (Anthropic)
  - OpenAI Codex
  - Other MCP-compatible agents (manual setup)

Getting started:

  1. Set up a project:
     cd your-project
     claude-co setup <server-url> <api-key> <group>

  2. Select your agent type when prompted

  3. Restart your AI agent in this directory

  4. The agent will have access to coordination tools!

Commands:
  setup        Configure a project for coordination
  setup-hooks  Install reminder hooks (Claude Code only)
  worker       Run autonomous worker mode
  run          Run MCP server (used internally by agents)

For more info: https://github.com/jude-hawrani/claude-co
""")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
