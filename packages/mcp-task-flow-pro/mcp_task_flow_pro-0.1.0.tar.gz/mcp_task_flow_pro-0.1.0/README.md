# MCP Task Flow Pro

A simple task management MCP for adding, completing, and tracking tasks

## Installation

```bash
uvx mcp-task-flow-pro
```

## Tools

- `add_task`: Add a new task
- `complete_task`: Mark a task as completed
- `get_stats`: Get productivity statistics

## Resources

- `tasks://list`: Current task list

## Prompts

- `daily_focus`: Generate a daily focus prompt

## Claude Desktop Configuration

```json
{
  "mcpServers": {
    "mcp-task-flow-pro": {
      "command": "uvx",
      "args": ["mcp-task-flow-pro"]
    }
  }
}
```

---

Generated with MCP Builder
