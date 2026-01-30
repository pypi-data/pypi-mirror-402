# mcp-habitica

A Model Context Protocol (MCP) server for [Habitica](https://habitica.com/) - enabling Claude to manage your tasks and tags.

## Features

This MCP server provides tools for managing Habitica tasks and tags:

### Task Operations
- **get_tasks** - Get all tasks or filter by type (habits, dailys, todos, rewards)
- **get_task** - Get a specific task by ID
- **create_task** - Create a new task with title, notes, tags, and priority
- **update_task** - Update an existing task
- **delete_task** - Delete a task
- **score_task** - Mark a task as complete or failed

### Tag Operations
- **get_tags** - Get all tags
- **get_tag** - Get a specific tag by ID
- **create_tag** - Create a new tag
- **update_tag** - Update a tag name
- **delete_tag** - Delete a tag

## Installation

### Using uv (recommended)

```bash
# Install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install the package
uvx mcp-habitica
```

### Using pip

```bash
pip install mcp-habitica
```

## Configuration

### 1. Get Your Habitica API Credentials

1. Log in to [Habitica](https://habitica.com/)
2. Go to **Settings** > **Site Data**
3. Copy your **User ID** and **API Token**

### 2. Configure Environment Variables

Set the following environment variables:

```bash
export HABITICA_USER_ID="your-user-id"
export HABITICA_API_TOKEN="your-api-token"
```

### 3. Configure Claude Desktop

Add this to your Claude Desktop configuration file:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "habitica": {
      "command": "uv",
      "args": ["mcp-habitica"],
      "env": {
        "HABITICA_USER_ID": "your-user-id",
        "HABITICA_API_TOKEN": "your-api-token"
      }
    }
  }
}
```

### to run locally
```json
{
  "mcpServers": {
    "mcp-habitica": {
      "command": "uv",
      "args": [
        "--directory",
        "<repo-folder>/mcp-habitica",
        "run",
        "mcp-habitica"
      ],
      "env": {
        "HABITICA_USER_ID": "your-user-id",
        "HABITICA_API_TOKEN": "your-api-token"
      }
    }
  }
}
```

## Usage Examples

Once configured, you can ask Claude to manage your Habitica tasks:

- "Show me all my todos"
- "Create a todo: Finish the project report"
- "Mark task [task-id] as complete"
- "Create a tag called 'work'"
- "Show all my tags"

## API Reference

For detailed API documentation, visit the [Habitica API Documentation](https://habitica.com/apidoc/).

### Task Types

- `habit` - Habits (positive/negative)
- `daily` - Daily tasks
- `todo` - To-dos
- `reward` - Rewards

### Task Priority Levels

- `0.1` - Trivial
- `1.0` - Easy (default)
- `1.5` - Medium
- `2.0` - Hard

## Development

### Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/mcp-habitica.git
cd mcp-habitica

# Install dependencies
uv sync

# Run tests (when available)
uv run pytest
```

### Project Structure

```
mcp-habitica/
├── src/
│   └── mcp_habitica/
│       ├── __init__.py
│       ├── habitica_client.py  # Habitica API client
│       └── server.py            # MCP server implementation
├── pyproject.toml
├── README.md
└── LICENSE
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with the [Model Context Protocol SDK](https://github.com/anthropics/mcp)
- Inspired by [mcp-obsidian](https://github.com/MarkusPfundstein/mcp-obsidian)
- Uses the [Habitica API](https://habitica.com/apidoc/)
