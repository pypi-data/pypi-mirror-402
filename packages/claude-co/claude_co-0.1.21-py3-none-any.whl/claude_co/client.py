"""HTTP client for the Claude-Co coordination server."""

import json
import os
import socket
from dataclasses import dataclass
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from typing import Optional


def find_config_file() -> Optional[Path]:
    """
    Find .claude-co.json config file by searching:
    1. Current directory and parents (up to home or root)
    2. ~/.claude-co/current.json (most recently configured project)
    3. ~/.claude-co/config.json (global config)
    """
    current = Path.cwd()
    home = Path.home()

    while current != current.parent:
        config_path = current / ".claude-co.json"
        if config_path.exists():
            return config_path
        if current == home:
            break
        current = current.parent

    # Check for "current" project (set by most recent setup_connection)
    current_config = home / ".claude-co" / "current.json"
    if current_config.exists():
        return current_config

    # Fallback to global config
    user_config = home / ".claude-co" / "config.json"
    if user_config.exists():
        return user_config

    return None


def load_config() -> dict:
    """Load configuration from .claude-co.json file."""
    config_path = find_config_file()
    if config_path:
        try:
            with open(config_path) as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return {}


DEFAULT_FALLBACK_URL = "http://localhost:8000"


def normalize_server_url(server_url: str) -> str:
    if not server_url:
        return server_url
    if "://" in server_url:
        return server_url
    return f"http://{server_url}"


class CoordinatorClient:
    """
    HTTP client for the Claude-Co coordination server.

    Configuration priority (highest to lowest):
    1. Constructor arguments
    2. .claude-co.json file (in project or ~/.claude-co/config.json)
    3. Environment variables
    """
    def __init__(self, base_url: str = None, agent_id: str = None, agent_name: str = None,
                 api_key: str = None, group: str = None, codebase: str = None):
        config = load_config()

        # URL: constructor > config > env > default
        if base_url:
            self.base_url = normalize_server_url(base_url)
        elif config.get("url"):
            self.base_url = normalize_server_url(config["url"])
        elif os.environ.get("COORDINATOR_URL"):
            self.base_url = normalize_server_url(os.environ["COORDINATOR_URL"])
        else:
            self.base_url = DEFAULT_FALLBACK_URL

        # Agent identity
        self.agent_id = agent_id or config.get("agent_id") or os.environ.get("AGENT_ID")
        self.agent_name = agent_name or config.get("agent_name") or os.environ.get("AGENT_NAME", "Unknown")

        # Authentication
        self.api_key = api_key or config.get("api_key") or os.environ.get("COORDINATOR_API_KEY")
        self.group = group or config.get("group") or os.environ.get("COORDINATOR_GROUP")
        self.codebase = codebase or config.get("codebase") or os.environ.get("COORDINATOR_CODEBASE")

    def _request(self, method: str, endpoint: str, data: dict = None) -> dict:
        url = f"{self.base_url}{endpoint}"
        headers = {"Content-Type": "application/json"}

        if self.api_key:
            headers["X-API-Key"] = self.api_key
        if self.group:
            headers["X-Group"] = self.group
        if self.codebase:
            headers["X-Codebase"] = self.codebase

        body = json.dumps(data).encode() if data else None
        req = Request(url, data=body, headers=headers, method=method)

        try:
            with urlopen(req, timeout=10) as resp:
                return json.loads(resp.read().decode())
        except HTTPError as e:
            error_body = e.read().decode()
            try:
                error_data = json.loads(error_body)
                raise Exception(f"API error {e.code}: {error_data.get('detail', error_body)}")
            except json.JSONDecodeError:
                raise Exception(f"API error {e.code}: {error_body}")

    # --- Agent Methods ---

    def register(self, agent_id: str, name: str, agent_type: str = "claude-code") -> dict:
        self.agent_id = agent_id
        return self._request("POST", "/agents/register", {
            "id": agent_id, "name": name, "type": agent_type
        })

    def update_status(self, status: str = "online", working_on: str = None) -> dict:
        return self._request("POST", f"/agents/{self.agent_id}/status", {
            "status": status, "working_on": working_on
        })

    def list_agents(self) -> list:
        return self._request("GET", "/agents")

    def get_agent(self, agent_id: str) -> dict:
        return self._request("GET", f"/agents/{agent_id}")

    def heartbeat(self) -> dict:
        """Send heartbeat to keep agent marked as online."""
        if not self.agent_id:
            raise ValueError("Not registered")
        return self._request("POST", f"/agents/{self.agent_id}/heartbeat")

    # --- Message Methods ---

    def send_message(self, to: str, content: str, message_type: str = "chat") -> dict:
        return self._request("POST", "/messages", {
            "from_agent": self.agent_id, "to_agent": to,
            "content": content, "message_type": message_type
        })

    def get_messages(self, unread_only: bool = False) -> list:
        endpoint = f"/messages?for={self.agent_id}"
        if unread_only:
            endpoint += "&unread_only=true"
        return self._request("GET", endpoint)

    def mark_read(self, message_id: int) -> dict:
        return self._request("POST", f"/messages/{message_id}/read")

    # --- Task Methods ---

    def create_task(self, title: str, description: str = None) -> dict:
        return self._request("POST", "/tasks", {
            "title": title, "description": description, "created_by": self.agent_id
        })

    def list_tasks(self, status: str = None) -> list:
        endpoint = "/tasks"
        if status:
            endpoint += f"?status={status}"
        return self._request("GET", endpoint)

    def get_task(self, task_id: int) -> dict:
        return self._request("GET", f"/tasks/{task_id}")

    def assign_task(self, task_id: int, agent_id: str = None) -> dict:
        return self._request("POST", f"/tasks/{task_id}/assign", {
            "agent_id": agent_id or self.agent_id
        })

    def complete_task(self, task_id: int) -> dict:
        return self._request("POST", f"/tasks/{task_id}/complete")

    # --- Direction Methods ---

    def update_direction(self, current_goal: str = None, current_approach: str = None,
                        potential_conflicts: str = None, vision: str = None,
                        conversation_summary: str = None) -> dict:
        return self._request("PUT", f"/directions/{self.agent_id}", {
            "current_goal": current_goal, "current_approach": current_approach,
            "potential_conflicts": potential_conflicts, "vision": vision,
            "conversation_summary": conversation_summary
        })

    def get_direction(self, agent_id: str) -> dict:
        return self._request("GET", f"/directions/{agent_id}")

    def get_all_directions(self) -> list:
        return self._request("GET", "/directions")

    def add_direction_log(self, direction_type: str, content: str,
                         reason: str = None, related_files: str = None) -> dict:
        return self._request("POST", "/direction-log", {
            "agent_id": self.agent_id, "direction_type": direction_type,
            "content": content, "reason": reason, "related_files": related_files
        })

    # --- File Claim Methods ---

    def claim_file(self, file_path: str, claim_type: str = "editing", description: str = None) -> dict:
        return self._request("POST", "/file-claims", {
            "agent_id": self.agent_id, "file_path": file_path,
            "claim_type": claim_type, "description": description
        })

    def release_claim(self, claim_id: int) -> dict:
        return self._request("DELETE", f"/file-claims/{claim_id}")

    def release_all_claims(self) -> dict:
        return self._request("DELETE", f"/file-claims/by-agent/{self.agent_id}")

    def list_claims(self, agent_id: str = None) -> list:
        endpoint = "/file-claims"
        if agent_id:
            endpoint += f"?agent_id={agent_id}"
        return self._request("GET", endpoint)

    def check_file(self, file_path: str) -> dict:
        return self._request("GET", f"/file-claims/check/{file_path}")

    # --- Change Journal Methods ---

    def record_change(self, change_type: str, description: str,
                     files_affected: str = None, semantic_impact: str = None) -> dict:
        return self._request("POST", "/change-journal", {
            "agent_id": self.agent_id, "change_type": change_type,
            "description": description, "files_affected": files_affected,
            "semantic_impact": semantic_impact
        })

    def get_changes(self, agent_id: str = None, hours: int = 24) -> list:
        endpoint = f"/change-journal?hours={hours}"
        if agent_id:
            endpoint += f"&agent_id={agent_id}"
        return self._request("GET", endpoint)

    # --- Team Awareness Methods ---

    def get_team_awareness(self) -> dict:
        return self._request("GET", "/team-awareness")

    def get_project_summary(self) -> dict:
        return self._request("GET", "/project-summary")

    def get_status_markdown(self) -> str:
        url = f"{self.base_url}/status.md"
        headers = {}
        if self.api_key:
            headers["X-API-Key"] = self.api_key
        if self.group:
            headers["X-Group"] = self.group
        if self.codebase:
            headers["X-Codebase"] = self.codebase
        req = Request(url, headers=headers, method="GET")
        with urlopen(req, timeout=10) as resp:
            return resp.read().decode()

    # --- Discussion Methods ---

    def create_discussion(self, title: str, topic: str, with_agents: list,
                         conflict_type: str = None, related_files: str = None,
                         initial_argument: str = None) -> dict:
        return self._request("POST", "/discussions", {
            "title": title, "topic": topic, "initiated_by": self.agent_id,
            "with_agents": with_agents, "conflict_type": conflict_type,
            "related_files": related_files, "initial_argument": initial_argument
        })

    def list_discussions(self, status: str = None, agent_id: str = None) -> list:
        params = []
        if status:
            params.append(f"status={status}")
        if agent_id:
            params.append(f"agent_id={agent_id}")
        query = "?" + "&".join(params) if params else ""
        return self._request("GET", f"/discussions{query}")

    def get_discussion(self, discussion_id: int) -> dict:
        return self._request("GET", f"/discussions/{discussion_id}")

    def add_discussion_message(self, discussion_id: int, content: str,
                               message_type: str = "argument") -> dict:
        return self._request("POST", f"/discussions/{discussion_id}/messages", {
            "from_agent": self.agent_id, "content": content, "message_type": message_type
        })

    def request_human_input(self, discussion_id: int) -> dict:
        return self._request("POST", f"/discussions/{discussion_id}/request-human?agent_id={self.agent_id}")

    def propose_resolution(self, discussion_id: int, summary: str, action_items: str = None) -> dict:
        return self._request("POST", f"/discussions/{discussion_id}/propose-resolution", {
            "proposed_by": self.agent_id, "summary": summary, "action_items": action_items
        })

    def resolve_discussion(self, discussion_id: int, resolution_summary: str) -> dict:
        from urllib.parse import quote
        return self._request("POST",
            f"/discussions/{discussion_id}/resolve?resolved_by={self.agent_id}&resolution_summary={quote(resolution_summary)}")

    def get_active_discussions(self) -> list:
        return self._request("GET", f"/discussions/active/for-agent/{self.agent_id}")

    # --- Learning Methods ---

    def record_learning(self, category: str, situation: str, action: str,
                       outcome: str, tags: str = None) -> dict:
        return self._request("POST", "/learnings", {
            "recorded_by": self.agent_id, "category": category,
            "situation": situation, "action": action, "outcome": outcome, "tags": tags
        })

    def search_learnings(self, category: str = None, tag: str = None, search: str = None) -> list:
        params = []
        if category:
            params.append(f"category={category}")
        if tag:
            params.append(f"tag={tag}")
        if search:
            params.append(f"search={search}")
        query = "?" + "&".join(params) if params else ""
        return self._request("GET", f"/learnings{query}")

    def upvote_learning(self, learning_id: int) -> dict:
        return self._request("POST", f"/learnings/{learning_id}/upvote")
