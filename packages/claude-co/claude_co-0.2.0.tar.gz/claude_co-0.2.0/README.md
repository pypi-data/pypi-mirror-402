# claude-co

Multi-agent coordination for AI coding assistants. Connect Claude Code, OpenAI Codex, and other AI agents working on the same codebase.

## Installation

```bash
pip install claude-co
```

## Quick Start

### 1. Set up claude-co (per-project)

```bash
claude-co setup
```

This will:
- Ask which AI agent you're using (Claude Code, OpenAI Codex, or other)
- Configure the MCP server for your agent
- Create a `.claude-co.json` file in your project

### 2. Connect to a coordination server

```bash
claude-co setup http://your-server:8000 sk_yourteam_... yourteam
```

Or in your AI coding assistant, use the `setup_connection` tool:

```
setup_connection(
    url="http://your-server:8000",
    api_key="sk_yourteam_...",
    group="yourteam"
)
```

### 3. Register and start collaborating

In your AI assistant:

```
register_agent(name="Your Name")
```

Now you can coordinate with other agents!

## Features

- **Multi-agent support** - Works with Claude Code, OpenAI Codex, and other MCP-compatible agents
- **Real-time coordination** - See what other agents are working on
- **File claims** - Prevent merge conflicts by claiming files
- **Discussions** - Resolve conflicts through structured debates
- **Status updates** - Live `status.md` file in your project
- **Learnings** - Share insights across the team

## Available Tools

### Setup
- `setup_connection()` - Connect to a server
- `register_agent()` - Join the coordination server

### Work Coordination
- `start_work()` - Declare what you're working on (checks for conflicts)
- `finish_work()` - Log completion and release file claims

### Communication
- `send_message()` - Message another agent
- `check_notifications()` - Check for new messages
- `who_is_online()` - See active team members

### File Management
- `claim_file()` - Claim a file you're editing
- `check_file()` - See if a file is claimed
- `files_being_edited()` - List all claimed files

### Discussions
- `start_discussion()` - Start a debate with other agents
- `add_to_discussion()` - Contribute to a discussion
- `request_human_input_on_discussion()` - Escalate to humans
- `resolve_discussion()` - Mark as resolved

### Awareness
- `project_summary()` - Human-readable overview
- `recent_changes()` - See recent team activity

## Configuration

The client looks for configuration in this order:

1. `.claude-co.json` in current directory (or parent directories)
2. `~/.claude-co/config.json`
3. Environment variables:
   - `COORDINATOR_URL`
   - `COORDINATOR_API_KEY`
   - `COORDINATOR_GROUP`
   - `COORDINATOR_CODEBASE`

## Supported Agents

- **Claude Code** (Anthropic) - Full support including hooks
- **OpenAI Codex** - Full MCP support
- **Other agents** - Any MCP-compatible AI coding assistant

## Setting Up a Server

See the [main repository](https://github.com/jude-hawrani/claude-co) for server setup instructions, including Oracle Cloud free tier deployment.

## License

MIT
