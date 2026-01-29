# n8n Advisor

MCP server for n8n workflow management. Provides AI assistants with the ability to review workflow status in n8n instances.

## Features

- **check_workflows**: Reviews all workflows and reports their status, including active/inactive counts and workflows with recent errors.

## Installation

```bash
pip install m2ai-mcp-n8n-advisor
```

## Configuration

Create a `.env` file or set environment variables:

```bash
# Base URL of your n8n instance (no trailing slash)
N8N_BASE_URL=https://your-n8n-instance.app.n8n.cloud

# API key from n8n Settings > API
N8N_API_KEY=your_api_key_here
```

### Getting Your n8n API Key

1. Open your n8n instance
2. Go to **Settings** > **API**
3. Create a new API key or copy an existing one
4. Use the full URL of your n8n instance for `N8N_BASE_URL`

## Usage

### Claude Desktop Configuration

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "n8n": {
      "command": "n8n-advisor",
      "env": {
        "N8N_BASE_URL": "https://your-n8n-instance.app.n8n.cloud",
        "N8N_API_KEY": "your_api_key_here"
      }
    }
  }
}
```

Or run directly with Python:

```json
{
  "mcpServers": {
    "n8n": {
      "command": "python",
      "args": ["-m", "n8n_mcp.server"],
      "env": {
        "N8N_BASE_URL": "https://your-n8n-instance.app.n8n.cloud",
        "N8N_API_KEY": "your_api_key_here"
      }
    }
  }
}
```

## Available Tools

### check_workflows

Reviews all workflows and reports their status.

**Parameters**: None

**Returns**:
- `total_workflows`: Total number of workflows
- `active_workflows`: Number of active workflows
- `inactive_workflows`: Number of inactive workflows
- `workflows_with_errors`: Count of workflows with recent errors
- `error_workflows`: List of workflows with errors (id, name, error count)
- `workflows`: Detailed list of all workflows with execution stats

**Example Response**:
```json
{
  "total_workflows": 5,
  "active_workflows": 3,
  "inactive_workflows": 2,
  "workflows_with_errors": 1,
  "error_workflows": [
    {"id": "2", "name": "Data Sync", "errors": 3}
  ],
  "workflows": [
    {
      "id": "1",
      "name": "Email Notifications",
      "active": true,
      "recent_executions": {
        "success": 10,
        "error": 0,
        "waiting": 0,
        "running": 0
      }
    }
  ]
}
```

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run tests with coverage
pytest --cov=n8n_mcp

# Type checking
mypy src/

# Linting
ruff check src/
```

## License

MIT
