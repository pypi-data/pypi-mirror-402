"""MCP server for Claude-Co multi-agent coordination."""

import os
import json
import threading
from pathlib import Path
from typing import Optional, Any
from functools import wraps
from mcp.server.fastmcp import FastMCP

from .client import CoordinatorClient, find_config_file, load_config


# ============================================================================
# URGENT NOTIFICATION SYSTEM
# ============================================================================
# Every tool response includes pending discussions/conflicts so agents can't miss them

def get_urgent_notifications() -> dict:
    """Get urgent items that agents MUST see - injected into every tool response."""
    if not client.agent_id:
        return {}

    urgent = {
        "_urgent_notifications": [],
        "_has_urgent": False
    }

    try:
        # Get active discussions
        discussions = client.list_discussions(agent_id=client.agent_id)
        active = [d for d in discussions if d.get("status") in ("open", "needs_human")]

        if active:
            urgent["_has_urgent"] = True
            for d in active:
                status_marker = "⚠️ NEEDS HUMAN INPUT" if d.get("status") == "needs_human" else "🔴 ACTIVE"
                urgent["_urgent_notifications"].append({
                    "type": "discussion",
                    "status": status_marker,
                    "id": d.get("id"),
                    "title": d.get("title"),
                    "topic": d.get("topic"),
                    "message": f"{status_marker}: Discussion #{d.get('id')} '{d.get('title')}' needs your response!"
                })

        # Get unread messages
        messages = client.get_messages(unread_only=True)
        if messages:
            urgent["_has_urgent"] = True
            urgent["_urgent_notifications"].append({
                "type": "messages",
                "count": len(messages),
                "message": f"📬 You have {len(messages)} unread message(s) from other agents!"
            })

    except Exception:
        pass  # Don't let notification errors break tools

    if urgent["_has_urgent"]:
        urgent["_action_required"] = "⚡ ACTION REQUIRED: Address the above notifications before continuing work!"

    return urgent if urgent["_has_urgent"] else {}


def inject_notifications(result: Any) -> Any:
    """Inject urgent notifications into a tool result."""
    notifications = get_urgent_notifications()

    if not notifications:
        return result

    # If result is a dict, add notifications
    if isinstance(result, dict):
        return {**notifications, **result}

    # If result is a list, wrap it
    if isinstance(result, list):
        return {**notifications, "result": result}

    # For other types, wrap in dict
    return {**notifications, "result": result}

# Initialize MCP server
mcp = FastMCP(
    "Claude-Co",
    instructions="""You have access to the Claude-Co coordination system for multi-agent collaboration.

FIRST: Call register_agent with your name to join the coordination server.

═══════════════════════════════════════════════════════════════════
CRITICAL: CHECK FOR DISCUSSIONS FIRST - EVERY SINGLE TIME
═══════════════════════════════════════════════════════════════════

Before responding to ANY user message, you MUST:

1. Call check_for_discussions() to see if other agents have raised concerns
2. Call check_notifications() to see if you have unread messages

If there are active discussions:
- READ the full discussion with get_discussion(id)
- RESPOND with your perspective using add_to_discussion()
- If you disagree, ARGUE your position clearly and respectfully
- If you're stuck or need guidance, call request_human_input_on_discussion()
- Tell your human about the disagreement and ask for their input

DO NOT ignore other agents. Collaboration requires engagement!

═══════════════════════════════════════════════════════════════════
WORKFLOW FOR TASKS:
═══════════════════════════════════════════════════════════════════

1. BEFORE any coding work, call:
   start_work(goal="what you're doing", approach="how", files_ill_touch="file1,file2")

2. AFTER completing work, call:
   finish_work(description="what you did", files_changed="...", semantic_impact="...")

═══════════════════════════════════════════════════════════════════

DISCUSSION TOOLS:
- check_for_discussions() - See active debates that need your attention
- my_discussions() - List all discussions you're part of
- get_discussion(id) - Read full discussion thread
- add_to_discussion(id, content) - Add your argument
- start_discussion(title, topic, with_agents) - Start a new debate
- request_human_input_on_discussion(id) - Escalate to your human
- propose_resolution(id, summary) - Suggest how to resolve
- resolve_discussion(id, summary) - Mark as resolved

OTHER TOOLS:
- project_summary() - Overview of what's happening
- send_message(to, content) - Message another agent
- check_notifications() - Check for messages
"""
)

# Initialize client
client = CoordinatorClient()


class StatusFileManager:
    """Keeps local status.md updated with live project status."""

    def __init__(self, client: CoordinatorClient, update_interval: int = 5):
        self.client = client
        self.update_interval = update_interval
        self.running = False
        self._thread: Optional[threading.Thread] = None
        self.status_path: Optional[Path] = None
        self._last_content: Optional[str] = None
        self._last_error: Optional[str] = None

    def _find_project_root(self) -> Path:
        # First, check if config has explicit project_path
        config = load_config()
        if config.get("project_path"):
            return Path(config["project_path"])

        # Fallback: use config file's directory
        config_path = find_config_file()
        if config_path:
            return config_path.parent

        # Last resort: walk up from cwd looking for .git or .claude-co.json
        current = Path.cwd()
        home = Path.home()

        while current != current.parent:
            if (current / ".git").exists():
                return current
            if (current / ".claude-co.json").exists():
                return current
            if current == home:
                break
            current = current.parent
        return Path.cwd()

    def start(self):
        if self.running:
            return

        project_root = self._find_project_root()
        self.status_path = project_root / "status.md"
        self.running = True
        self._thread = threading.Thread(target=self._update_loop, daemon=True)
        self._thread.start()

        # Try an immediate update
        self._update_status()

    def stop(self):
        self.running = False

    def _update_loop(self):
        import time
        while self.running:
            # Send heartbeat to keep agent marked as online
            if self.client.agent_id:
                try:
                    self.client.heartbeat()
                except Exception:
                    pass  # Heartbeat failed, but keep trying
            try:
                self._update_status()
            except Exception as e:
                self._last_error = str(e)
            time.sleep(self.update_interval)

    def _update_status(self):
        try:
            content = self.client.get_status_markdown()
            if content != self._last_content:
                self.status_path.write_text(content)
                self._last_content = content
                self._last_error = None
        except Exception as e:
            self._last_error = str(e)

    def force_update(self) -> dict:
        """Force an immediate status update and return debug info."""
        config = load_config()
        config_path = find_config_file()

        result = {
            "config_file": str(config_path) if config_path else None,
            "project_path_from_config": config.get("project_path"),
            "status_path": str(self.status_path) if self.status_path else None,
            "running": self.running,
            "last_error": self._last_error,
        }

        try:
            content = self.client.get_status_markdown()
            result["fetch_status"] = "ok"
            result["content_length"] = len(content)

            if self.status_path:
                self.status_path.write_text(content)
                result["write_status"] = "ok"
                self._last_content = content
                self._last_error = None
            else:
                result["write_status"] = "no status_path set"
        except Exception as e:
            result["error"] = str(e)
            self._last_error = str(e)

        return result


# Status file manager
status_manager: Optional[StatusFileManager] = None


# --- Setup Tools ---

@mcp.tool()
def setup_connection(url: str, api_key: str, group: str, codebase: str = None,
                    save_globally: bool = False) -> dict:
    """
    Set up connection to a Claude-Co coordination server.
    Creates a .claude-co.json config file.

    Args:
        url: Server URL (e.g., "http://your-server:8000")
        api_key: Your API key
        group: Your group name
        codebase: Project name (defaults to current directory name)
        save_globally: If True, saves to ~/.claude-co/config.json

    Example:
        setup_connection(
            url="http://145.241.207.52:8000",
            api_key="sk_myteam_abc123...",
            group="myteam"
        )
    """
    if not codebase:
        codebase = Path.cwd().name

    # Store absolute project path so status.md can be written correctly
    project_path = str(Path.cwd().absolute())
    config = {"url": url, "api_key": api_key, "group": group, "codebase": codebase, "project_path": project_path}

    if save_globally:
        config_dir = Path.home() / ".claude-co"
        config_dir.mkdir(exist_ok=True)
        config_path = config_dir / "config.json"
    else:
        config_path = Path.cwd() / ".claude-co.json"

    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)

    # Also save as "current" project so MCP server can always find it
    current_dir = Path.home() / ".claude-co"
    current_dir.mkdir(exist_ok=True)
    with open(current_dir / "current.json", "w") as f:
        json.dump(config, f, indent=2)

    # Update client
    global client
    client.base_url = url
    client.api_key = api_key
    client.group = group
    client.codebase = codebase

    return {
        "status": "configured",
        "config_file": str(config_path),
        "message": f"Saved to {config_path}. Now call register_agent() to join."
    }


@mcp.tool()
def show_connection() -> dict:
    """Show current connection configuration."""
    config_path = find_config_file()
    return {
        "config_file": str(config_path) if config_path else None,
        "url": client.base_url,
        "group": client.group,
        "codebase": client.codebase,
        "api_key_set": bool(client.api_key),
        "agent_id": client.agent_id
    }


# --- Agent Tools ---

@mcp.tool()
def register_agent(name: str, agent_type: str = "claude-code") -> dict:
    """
    Register with the coordination server. Call this first!

    Args:
        name: Your name (e.g., "James")
        agent_type: Type of agent ("claude-code", "codex", etc.)

    Returns:
        Your agent info including assigned ID
    """
    global status_manager

    agent_id = os.environ.get("AGENT_ID")
    if not agent_id:
        raise ValueError("AGENT_ID environment variable not set")

    result = client.register(agent_id, name, agent_type)
    actual_id = result.get("id", agent_id)
    client.agent_id = actual_id

    # Start status file updates
    status_manager = StatusFileManager(client)
    status_manager.start()

    # Add helpful info
    if status_manager.status_path:
        result["status_file"] = str(status_manager.status_path)

    # Get team status
    try:
        agents = client.list_agents()
        online = [a for a in agents if a.get("status") == "online" and a["id"] != actual_id]
        if online:
            result["_team"] = "TEAM ONLINE:\n" + "\n".join(
                f"- {a['id']} ({a['name']})" for a in online
            )
    except Exception:
        pass

    return result


@mcp.tool()
def update_status(status: str = "online", working_on: str = None) -> dict:
    """Update your status and what you're working on."""
    return client.update_status(status, working_on)


@mcp.tool()
def list_agents() -> list:
    """List all registered agents."""
    return client.list_agents()


# --- Messaging Tools ---

@mcp.tool()
def send_message(to: str, content: str, message_type: str = "chat") -> dict:
    """
    Send a message to another agent.

    Args:
        to: Agent ID or "*" for broadcast
        content: Message content
        message_type: "chat", "question", or "answer"
    """
    return client.send_message(to, content, message_type)


@mcp.tool()
def get_messages(unread_only: bool = False) -> list:
    """Get messages sent to you."""
    return client.get_messages(unread_only)


@mcp.tool()
def check_notifications() -> dict:
    """Check for new messages and discussions."""
    messages = client.get_messages(unread_only=True)
    discussions = []
    try:
        discussions = client.get_active_discussions()
    except Exception:
        pass

    if not messages and not discussions:
        return {"status": "No new notifications"}

    result = {}
    if messages:
        result["unread_messages"] = len(messages)
        result["messages"] = messages[:5]
    if discussions:
        result["active_discussions"] = len(discussions)
        result["discussions"] = discussions

    return result


# --- Task Tools ---

@mcp.tool()
def create_task(title: str, description: str = None) -> dict:
    """Create a new task."""
    return client.create_task(title, description)


@mcp.tool()
def list_tasks(status: str = None) -> list:
    """List tasks, optionally filtered by status."""
    return client.list_tasks(status)


@mcp.tool()
def pick_up_task(task_id: int) -> dict:
    """Assign a task to yourself."""
    return client.assign_task(task_id)


@mcp.tool()
def complete_task(task_id: int) -> dict:
    """Mark a task as complete."""
    return client.complete_task(task_id)


# --- Work Coordination Tools ---

@mcp.tool()
def start_work(goal: str, approach: str, files_ill_touch: str = None, vision: str = None) -> dict:
    """
    CALL THIS BEFORE STARTING WORK. Sets your direction and checks for conflicts.

    Args:
        goal: What you're trying to accomplish
        approach: How you plan to do it
        files_ill_touch: Comma-separated files you'll edit
        vision: Your vision for the project direction

    Returns:
        Status and any conflict warnings
    """
    warnings = []
    claimed_files = []
    conflicting_agents = []

    # Check for conflicts
    try:
        awareness = client.get_team_awareness()

        for agent in awareness.get("agents", []):
            if agent["id"] != client.agent_id:
                other_goal = agent.get("current_goal")
                other_conflicts = agent.get("potential_conflicts")

                if other_goal and files_ill_touch and other_conflicts:
                    my_files = set(f.strip() for f in files_ill_touch.split(","))
                    their_files = set(f.strip() for f in other_conflicts.split(","))
                    overlap = my_files & their_files
                    if overlap:
                        warnings.append(f"CONFLICT: {agent['name']} is working on: {', '.join(overlap)}")
                        conflicting_agents.append({"agent_id": agent["id"], "files": list(overlap)})

        for claim in awareness.get("file_claims", []):
            if claim["agent_id"] != client.agent_id and files_ill_touch:
                if claim["file_path"] in files_ill_touch:
                    warnings.append(f"FILE CLAIMED: {claim['file_path']} by {claim['agent_id']}")
    except Exception as e:
        warnings.append(f"Could not check team state: {e}")

    # Set direction
    client.update_direction(
        current_goal=goal,
        current_approach=approach,
        potential_conflicts=files_ill_touch,
        vision=vision
    )

    # Log direction
    client.add_direction_log("goal", goal, approach, files_ill_touch)

    # Claim files
    if files_ill_touch:
        for file_path in files_ill_touch.split(","):
            file_path = file_path.strip()
            if file_path:
                try:
                    client.claim_file(file_path, "editing", goal)
                    claimed_files.append(file_path)
                except Exception as e:
                    warnings.append(f"Could not claim {file_path}: {e}")

    result = {
        "status": "ready" if not warnings else "ready_with_warnings",
        "goal": goal,
        "files_claimed": claimed_files,
    }

    if warnings:
        result["warnings"] = warnings
        if conflicting_agents:
            result["conflicting_agents"] = conflicting_agents
            result["suggestion"] = "Consider starting a discussion to coordinate"

    # Always inject urgent notifications so conflicts are visible
    return inject_notifications(result)


@mcp.tool()
def finish_work(description: str, files_changed: str = None, semantic_impact: str = None) -> dict:
    """
    CALL THIS WHEN DONE. Logs your changes and releases file claims.

    WARNING: This will check for unresolved discussions first! You should
    resolve any active discussions before finishing work.

    Args:
        description: What you accomplished
        files_changed: Comma-separated files you modified
        semantic_impact: What this change means for the system
    """
    warnings = []
    unresolved_discussions = []

    # Check for unresolved discussions before allowing completion
    try:
        discussions = client.list_discussions(agent_id=client.agent_id)
        active = [d for d in discussions if d.get("status") in ("open", "needs_human")]
        if active:
            for d in active:
                unresolved_discussions.append({
                    "id": d.get("id"),
                    "title": d.get("title"),
                    "status": d.get("status")
                })
            warnings.append(f"⚠️ WARNING: You have {len(active)} unresolved discussion(s)!")
            warnings.append("Consider resolving these before finishing your work:")
            for d in active:
                warnings.append(f"  - Discussion #{d.get('id')}: {d.get('title')}")
    except Exception:
        pass

    # Record change
    client.record_change("modified", description, files_changed, semantic_impact)

    # Release claims
    client.release_all_claims()

    # Log completion
    client.add_direction_log("completion", description, semantic_impact, files_changed)

    # Clear direction
    client.update_direction(current_goal=None, current_approach=None, potential_conflicts=None)

    result = {
        "status": "completed" if not unresolved_discussions else "completed_with_warnings",
        "description": description,
        "files_changed": files_changed,
        "claims_released": True
    }

    if warnings:
        result["warnings"] = warnings
        result["unresolved_discussions"] = unresolved_discussions
        result["recommendation"] = "Please address unresolved discussions to ensure all team members are aligned."

    return inject_notifications(result)


# --- File Claim Tools ---

@mcp.tool()
def claim_file(file_path: str, description: str = None) -> dict:
    """Claim a file you're about to edit."""
    return client.claim_file(file_path, "editing", description)


@mcp.tool()
def release_claims() -> dict:
    """Release all your file claims."""
    return client.release_all_claims()


@mcp.tool()
def check_file(file_path: str) -> dict:
    """Check if a file is claimed by anyone."""
    return client.check_file(file_path)


@mcp.tool()
def files_being_edited() -> list:
    """See all currently claimed files."""
    return client.list_claims()


# --- Discussion Tools ---

@mcp.tool()
def start_discussion(title: str, topic: str, with_agents: str,
                    conflict_type: str = None, initial_argument: str = None) -> dict:
    """
    Start a discussion/debate with other agents.

    Args:
        title: Short title
        topic: What the discussion is about
        with_agents: Comma-separated agent IDs
        conflict_type: "direction", "file", "approach", or "vision"
        initial_argument: Your opening statement
    """
    agent_list = [a.strip() for a in with_agents.split(",") if a.strip()]
    return client.create_discussion(title, topic, agent_list, conflict_type, None, initial_argument)


@mcp.tool()
def add_to_discussion(discussion_id: int, content: str, message_type: str = "argument") -> dict:
    """Add a message to a discussion."""
    return client.add_discussion_message(discussion_id, content, message_type)


@mcp.tool()
def get_discussion(discussion_id: int) -> dict:
    """Get full discussion details."""
    return client.get_discussion(discussion_id)


@mcp.tool()
def my_discussions() -> list:
    """List discussions you're involved in."""
    return client.list_discussions(agent_id=client.agent_id)


@mcp.tool()
def request_human_input_on_discussion(discussion_id: int) -> dict:
    """Request your human's input on a discussion."""
    return client.request_human_input(discussion_id)


@mcp.tool()
def propose_resolution(discussion_id: int, summary: str, action_items: str = None) -> dict:
    """Propose a resolution to a discussion."""
    return client.propose_resolution(discussion_id, summary, action_items)


@mcp.tool()
def resolve_discussion(discussion_id: int, resolution_summary: str) -> dict:
    """Mark a discussion as resolved."""
    return client.resolve_discussion(discussion_id, resolution_summary)


@mcp.tool()
def check_for_discussions() -> dict:
    """
    Check if you have any active discussions that need your attention.

    IMPORTANT: Call this at the START of every response to stay engaged
    with other agents. Ignoring discussions damages collaboration.

    Returns list of active discussions with unread messages or pending decisions.
    """
    discussions = client.list_discussions(agent_id=client.agent_id)
    # Filter to only show discussions that need attention
    active = [d for d in discussions if d.get("status") in ("open", "needs_human")]
    return {
        "active_discussions": active,
        "count": len(active),
        "needs_attention": len(active) > 0,
        "message": f"You have {len(active)} active discussion(s) requiring your attention." if active else "No active discussions."
    }


# --- Awareness Tools ---

@mcp.tool()
def project_summary() -> dict:
    """Get a human-readable summary of what's happening."""
    return client.get_project_summary()


@mcp.tool()
def debug_status_file() -> dict:
    """Debug tool: Force status.md update and show what's happening."""
    global status_manager

    if not status_manager:
        return {
            "error": "StatusFileManager not initialized. Call register_agent() first.",
            "config_file": str(find_config_file()),
            "config": load_config()
        }

    return status_manager.force_update()


@mcp.tool()
def who_is_online() -> list:
    """See who's online and what they're working on."""
    agents = client.list_agents()
    return [
        {"name": a["name"], "id": a["id"], "working_on": a.get("working_on")}
        for a in agents if a.get("status") == "online"
    ]


@mcp.tool()
def recent_changes(hours: int = 24) -> list:
    """Get recent changes from the team."""
    return client.get_changes(hours=hours)


# --- Learning Tools ---

@mcp.tool()
def record_learning(category: str, situation: str, action: str, outcome: str,
                   tags: str = None) -> dict:
    """
    Record something that worked well.

    Args:
        category: "coordination", "debugging", "code-review", etc.
        situation: What was the context?
        action: What did you do?
        outcome: What happened?
        tags: Comma-separated tags
    """
    return client.record_learning(category, situation, action, outcome, tags)


@mcp.tool()
def search_learnings(category: str = None, tag: str = None, search: str = None) -> list:
    """Search past learnings for insights."""
    return client.search_learnings(category, tag, search)


def main():
    mcp.run()


if __name__ == "__main__":
    main()
