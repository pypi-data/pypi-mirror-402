"""
MCP Task Flow Pro

A simple task management MCP for adding, completing, and tracking tasks
"""

from fastmcp import FastMCP

# Initialize the MCP server
mcp = FastMCP("MCP Task Flow Pro")

@mcp.tool()
def add_task(title: str, priority: str) -> str:
    """Add a new task

    Args:
        title: The task title
        priority: Task priority: low, medium, or high

    Returns:
        Task added confirmation
    """
    import time
    
    task_id = int(time.time())
    priority = priority or 'medium'
    
    result = 'Task added: ' + title + ' (Priority: ' + priority + ', ID: ' + str(task_id) + ')'
    return result

@mcp.tool()
def complete_task(task_id: int) -> str:
    """Mark a task as completed

    Args:
        task_id: The task ID to complete

    Returns:
        Task completion confirmation
    """
    import random
    
    messages = ['Great job!', 'Task completed!', 'Well done!', 'Keep it up!']
    message = random.choice(messages)
    
    return message + ' Task #' + str(task_id) + ' has been completed.'

@mcp.tool()
def get_stats(period: str) -> str:
    """Get productivity statistics

    Args:
        period: Time period: today, week, or month

    Returns:
        Productivity statistics
    """
    import random
    
    period = period or 'today'
    tasks = random.randint(1, 10)
    hours = random.randint(2, 8)
    
    stats = 'Stats for ' + period + ':\n'
    stats += 'Tasks completed: ' + str(tasks) + '\n'
    stats += 'Hours focused: ' + str(hours) + '\n'
    stats += 'Keep up the great work!'
    
    return stats

@mcp.resource("tasks://list")
def task_list() -> str:
    """Current task list"""
    import json
    
    tasks = [
        {'id': 1, 'title': 'Review project', 'completed': False},
        {'id': 2, 'title': 'Write report', 'completed': True},
        {'id': 3, 'title': 'Team meeting', 'completed': False}
    ]
    
    return json.dumps(tasks, indent=2)

@mcp.prompt()
def daily_focus(goal: str) -> str:
    """Generate a daily focus prompt

    Args:
        goal: Your main goal for today
    """
    return f"""Daily Focus Session

Goal: {{ goal or 'Make meaningful progress' }}

Action Steps:
1. Choose your top 3 priorities
2. Eliminate distractions
3. Work in focused blocks
4. Take regular breaks

You can do this! Stay focused and make it happen!"""

def main():
    """Entry point for the MCP server."""
    mcp.run()

if __name__ == "__main__":
    main()
