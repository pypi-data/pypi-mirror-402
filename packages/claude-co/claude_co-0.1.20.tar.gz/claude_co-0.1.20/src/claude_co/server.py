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
    instructions="""Claude-Co: Multi-agent coordination system.

SETUP: Call register_agent(name) first to join.

WORKFLOW:
1. Call check_inbox() at the START of every response
2. Before coding: start_work(goal, approach, files_ill_touch)
3. After coding: finish_work(description, files_changed)

KEY TOOLS:
- check_inbox() - Messages and discussions needing attention
- send_message(to, content) - Message another agent
- discussion(action, ...) - Manage discussions
- team_status() - See what the team is doing
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
    """List all registered agents and their status."""
    return client.list_agents()


# --- Messaging Tools ---

@mcp.tool()
def check_inbox(all_messages: bool = False) -> dict:
    """
    Check for messages and discussions needing your attention.

    IMPORTANT: Call this at the START of every response to stay
    engaged with your team. Ignoring messages damages collaboration.

    Args:
        all_messages: If True, return all messages (not just unread)

    Returns unread messages and active discussions by default.
    """
    result = {"status": "ok"}

    # Get messages
    msgs = client.get_messages(unread_only=not all_messages)
    if msgs:
        result["message_count"] = len(msgs)
        result["messages"] = msgs if all_messages else msgs[:5]

    # Get active discussions
    try:
        discussions = client.list_discussions(agent_id=client.agent_id)
        active = [d for d in discussions if d.get("status") in ("open", "needs_human")]
        if active:
            result["active_discussions"] = len(active)
            result["discussions"] = active
    except Exception:
        pass

    if "message_count" not in result and "active_discussions" not in result:
        result["message"] = "No messages or discussions need attention"

    return result


@mcp.tool()
def send_message(to: str, content: str, message_type: str = "chat") -> dict:
    """
    Send a message to another agent.

    Args:
        to: Agent ID (e.g., "james-claude") or "*" to broadcast to all
        content: Your message
        message_type: "chat", "question", or "answer"

    Examples:
        send_message("james-claude", "Can you review my PR?")
        send_message("*", "Starting work on auth module")  # broadcast
    """
    return client.send_message(to, content, message_type)


# --- Task Tools ---

@mcp.tool()
def task(
    action: str,
    id: int = None,
    title: str = None,
    description: str = None,
    status: str = None
) -> dict:
    """
    Manage the shared task board for coordinating work across agents.

    Workflow: list → pick_up → (do the work) → complete

    Actions:
    - "list": See all tasks (optional: status filter - "open"|"assigned"|"in_progress"|"done")
    - "create": Add a task for yourself or others (required: title; optional: description)
    - "pick_up": Claim a task to work on (required: id)
    - "complete": Mark your task as done (required: id)

    Examples:
        task("list")
        task("list", status="open")
        task("create", title="Fix login bug", description="Users can't login with SSO")
        task("pick_up", id=3)
        task("complete", id=3)
    """
    action = action.lower()

    if action == "list":
        return {"tasks": client.list_tasks(status)}

    elif action == "create":
        if not title:
            return {"error": "create requires: title"}
        return client.create_task(title, description)

    elif action == "pick_up":
        if not id:
            return {"error": "pick_up requires: id"}
        return client.assign_task(id)

    elif action == "complete":
        if not id:
            return {"error": "complete requires: id"}
        return client.complete_task(id)

    else:
        return {"error": f"Unknown action '{action}'. Use: list, create, pick_up, complete"}


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
def files(action: str, path: str = None, description: str = None) -> dict:
    """
    Check and manage file claims to avoid conflicts with other agents.

    Note: start_work() and finish_work() handle claims automatically.
    Use this tool to check what files others are editing before you start.

    Actions:
    - "list": See all files currently being edited by any agent
    - "check": Check if a specific file is claimed (required: path)
    - "claim": Manually claim a file (required: path; optional: description)
    - "release": Release all your file claims

    Examples:
        files("list")
        files("check", path="src/main.py")
        files("claim", path="src/main.py", description="refactoring")
        files("release")
    """
    action = action.lower()

    if action == "list":
        return {"files_being_edited": client.list_claims()}

    elif action == "check":
        if not path:
            return {"error": "check requires: path"}
        return client.check_file(path)

    elif action == "claim":
        if not path:
            return {"error": "claim requires: path"}
        return client.claim_file(path, "editing", description)

    elif action == "release":
        return client.release_all_claims()

    else:
        return {"error": f"Unknown action '{action}'. Use: list, check, claim, release"}


# --- Discussion Tools ---

@mcp.tool()
def discussion(
    action: str,
    id: int = None,
    title: str = None,
    topic: str = None,
    with_agents: str = None,
    content: str = None,
    conflict_type: str = None,
    resolution: str = None,
    action_items: str = None
) -> dict:
    """
    Manage discussions with other agents. All discussion operations in one tool.

    Actions:
    - "start": Start new discussion
        Required: title, topic, with_agents (comma-separated agent IDs)
        Optional: conflict_type ("direction"|"file"|"approach"|"vision"), content (opening argument)
    - "reply": Add message to discussion
        Required: id, content
    - "get": Get full discussion with all messages
        Required: id
    - "list": List all your discussions
    - "escalate": Request human input on stuck discussion
        Required: id
    - "propose": Propose a resolution
        Required: id, resolution
        Optional: action_items
    - "resolve": Mark discussion as resolved
        Required: id, resolution

    Examples:
        discussion("start", title="API approach", topic="REST vs GraphQL", with_agents="james-claude")
        discussion("reply", id=1, content="I agree, let's use REST")
        discussion("get", id=1)
        discussion("list")
        discussion("escalate", id=1)
        discussion("propose", id=1, resolution="Use REST for now, revisit later")
        discussion("resolve", id=1, resolution="Agreed to use REST")
    """
    action = action.lower()

    if action == "start":
        if not title or not topic or not with_agents:
            return {"error": "start requires: title, topic, with_agents"}
        agent_list = [a.strip() for a in with_agents.split(",") if a.strip()]
        return client.create_discussion(title, topic, agent_list, conflict_type, None, content)

    elif action == "reply":
        if not id or not content:
            return {"error": "reply requires: id, content"}
        return client.add_discussion_message(id, content, "argument")

    elif action == "get":
        if not id:
            return {"error": "get requires: id"}
        return client.get_discussion(id)

    elif action == "list":
        return client.list_discussions(agent_id=client.agent_id)

    elif action == "escalate":
        if not id:
            return {"error": "escalate requires: id"}
        return client.request_human_input(id)

    elif action == "propose":
        if not id or not resolution:
            return {"error": "propose requires: id, resolution"}
        return client.propose_resolution(id, resolution, action_items)

    elif action == "resolve":
        if not id or not resolution:
            return {"error": "resolve requires: id, resolution"}
        return client.resolve_discussion(id, resolution)

    else:
        return {"error": f"Unknown action '{action}'. Use: start, reply, get, list, escalate, propose, resolve"}


# --- Awareness Tools ---

@mcp.tool()
def team_status(include_changes: bool = False, hours: int = 24) -> dict:
    """
    Get a snapshot of what the team is doing right now.

    Use this to understand the current state before starting work:
    - Who's online and what they're working on
    - Overall project activity summary
    - Optionally: recent changes made by the team

    Args:
        include_changes: Include recent code changes (default: False)
        hours: How far back to look for changes (default: 24)

    Examples:
        team_status()
        team_status(include_changes=True)
        team_status(include_changes=True, hours=48)
    """
    # Get project summary
    result = client.get_project_summary()

    # Add who's online with details
    agents = client.list_agents()
    online = [
        {"name": a["name"], "id": a["id"], "working_on": a.get("working_on")}
        for a in agents if a.get("status") == "online"
    ]
    result["online_agents"] = online
    result["online_count"] = len(online)

    # Optionally include recent changes
    if include_changes:
        result["recent_changes"] = client.get_changes(hours=hours)

    return result


def main():
    mcp.run()


if __name__ == "__main__":
    main()
