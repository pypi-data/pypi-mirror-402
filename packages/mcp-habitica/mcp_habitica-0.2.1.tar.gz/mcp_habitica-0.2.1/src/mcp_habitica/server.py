"""MCP server implementation for Habitica."""

import asyncio
import os
import json
from typing import Any

import mcp.types as types
from mcp.server import Server
from mcp.server.stdio import stdio_server

from .habitica_client import HabiticaClient


# Initialize MCP server
app = Server("mcp-habitica")

# Global client instance
habitica_client: HabiticaClient | None = None


def get_client() -> HabiticaClient:
    """Get the Habitica client instance."""
    if habitica_client is None:
        raise RuntimeError("Habitica client not initialized")
    return habitica_client


def normalize_task(task: Any) -> Any:
    """Ensure task has consistent fields to avoid KeyError in client scripts."""
    if not isinstance(task, dict):
        return task

    # Habitica tasks can have missing fields depending on type
    # We ensure these exist to avoid KeyErrors in consumer scripts
    if "isDue" not in task:
        task["isDue"] = False
    if "completed" not in task:
        task["completed"] = False
    if "text" not in task:
        task["text"] = ""

    # Also normalize nested task objects (like in score_task response)
    if "task" in task and isinstance(task["task"], dict):
        task["task"] = normalize_task(task["task"])
    
    # Handle data wrapper structure
    if "data" in task and isinstance(task["data"], (dict, list)):
        if isinstance(task["data"], list):
            task["data"] = [normalize_task(t) for t in task["data"]]
        else:
            task["data"] = normalize_task(task["data"])

    return task


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    """List available Habitica tools."""
    return [
        # Task tools
        types.Tool(
            name="get_tasks",
            description="Get all tasks or filter by type (habits, dailys, todos, rewards)",
            inputSchema={
                "type": "object",
                "properties": {
                    "type": {
                        "type": "string",
                        "description": "Optional task type filter",
                        "enum": ["habits", "dailys", "todos", "rewards"],
                    }
                },
            },
        ),
        types.Tool(
            name="get_task",
            description="Get a specific task by ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "task_id": {
                        "type": "string",
                        "description": "The task ID",
                    }
                },
                "required": ["task_id"],
            },
        ),
        types.Tool(
            name="create_task",
            description="Create a new task",
            inputSchema={
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "Task title/description",
                    },
                    "type": {
                        "type": "string",
                        "description": "Task type",
                        "enum": ["habit", "daily", "todo", "reward"],
                        "default": "todo",
                    },
                    "notes": {
                        "type": "string",
                        "description": "Additional notes",
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of tag IDs",
                    },
                    "priority": {
                        "type": "number",
                        "description": "Priority: 0.1=trivial, 1=easy, 1.5=medium, 2=hard",
                        "default": 1.0,
                    },
                },
                "required": ["text"],
            },
        ),
        types.Tool(
            name="update_task",
            description="Update an existing task",
            inputSchema={
                "type": "object",
                "properties": {
                    "task_id": {
                        "type": "string",
                        "description": "The task ID",
                    },
                    "text": {
                        "type": "string",
                        "description": "New task title",
                    },
                    "notes": {
                        "type": "string",
                        "description": "New notes",
                    },
                    "priority": {
                        "type": "number",
                        "description": "New priority",
                    },
                },
                "required": ["task_id"],
            },
        ),
        types.Tool(
            name="delete_task",
            description="Delete a task",
            inputSchema={
                "type": "object",
                "properties": {
                    "task_id": {
                        "type": "string",
                        "description": "The task ID",
                    }
                },
                "required": ["task_id"],
            },
        ),
        types.Tool(
            name="score_task",
            description="Score a task (mark complete or fail)",
            inputSchema={
                "type": "object",
                "properties": {
                    "task_id": {
                        "type": "string",
                        "description": "The task ID",
                    },
                    "direction": {
                        "type": "string",
                        "description": "Score direction",
                        "enum": ["up", "down"],
                    },
                },
                "required": ["task_id", "direction"],
            },
        ),
        # Tag tools
        types.Tool(
            name="get_tags",
            description="Get all tags",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        types.Tool(
            name="get_tag",
            description="Get a specific tag by ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "tag_id": {
                        "type": "string",
                        "description": "The tag ID",
                    }
                },
                "required": ["tag_id"],
            },
        ),
        types.Tool(
            name="create_tag",
            description="Create a new tag",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Tag name",
                    }
                },
                "required": ["name"],
            },
        ),
        types.Tool(
            name="update_tag",
            description="Update an existing tag",
            inputSchema={
                "type": "object",
                "properties": {
                    "tag_id": {
                        "type": "string",
                        "description": "The tag ID",
                    },
                    "name": {
                        "type": "string",
                        "description": "New tag name",
                    },
                },
                "required": ["tag_id", "name"],
            },
        ),
        types.Tool(
            name="delete_tag",
            description="Delete a tag",
            inputSchema={
                "type": "object",
                "properties": {
                    "tag_id": {
                        "type": "string",
                        "description": "The tag ID",
                    }
                },
                "required": ["tag_id"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[types.TextContent]:
    """Handle tool calls."""
    client = get_client()

    try:
        # Task operations
        if name == "get_tasks":
            task_type = arguments.get("type")
            result = await client.get_tasks(task_type)
            result = [normalize_task(t) for t in result]
            return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "get_task":
            result = await client.get_task(arguments["task_id"])
            result = normalize_task(result)
            return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "create_task":
            result = await client.create_task(**arguments)
            result = normalize_task(result)
            return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "update_task":
            task_id = arguments.pop("task_id")
            result = await client.update_task(task_id, **arguments)
            result = normalize_task(result)
            return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "delete_task":
            result = await client.delete_task(arguments["task_id"])
            result = normalize_task(result)
            return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "score_task":
            result = await client.score_task(
                arguments["task_id"],
                arguments["direction"]
            )
            result = normalize_task(result)
            return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

        # Tag operations
        elif name == "get_tags":
            result = await client.get_tags()
            return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "get_tag":
            result = await client.get_tag(arguments["tag_id"])
            return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "create_tag":
            result = await client.create_tag(arguments["name"])
            return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "update_tag":
            result = await client.update_tag(
                arguments["tag_id"],
                arguments["name"]
            )
            return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "delete_tag":
            result = await client.delete_tag(arguments["tag_id"])
            return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

        else:
            raise ValueError(f"Unknown tool: {name}")

    except Exception as e:
        return [types.TextContent(type="text", text=f"Error: {str(e)}")]


async def run_server():
    """Run the MCP server."""
    global habitica_client

    # Get configuration from environment
    user_id = os.getenv("HABITICA_USER_ID")
    api_token = os.getenv("HABITICA_API_TOKEN")

    if not user_id or not api_token:
        raise ValueError(
            "HABITICA_USER_ID and HABITICA_API_TOKEN environment variables required"
        )

    # Initialize client
    habitica_client = HabiticaClient(user_id, api_token)

    try:
        async with stdio_server() as (read_stream, write_stream):
            await app.run(
                read_stream,
                write_stream,
                app.create_initialization_options(),
            )
    finally:
        if habitica_client:
            await habitica_client.close()


def main():
    """Entry point for the server."""
    asyncio.run(run_server())


if __name__ == "__main__":
    main()
