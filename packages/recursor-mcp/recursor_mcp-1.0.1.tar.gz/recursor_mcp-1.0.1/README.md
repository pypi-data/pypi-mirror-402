# Recursor MCP Server

Model Context Protocol (MCP) server for Recursor, enabling AI agents to search memory, record corrections, and check code safety.

## Features

- **Memory Search**: Find relevant coding patterns and past corrections.
- **Correction Recording**: Learn from user feedback to avoid repeating mistakes.
- **Safety Checks**: Validate code against safety guardrails.
- **Dual Mode**: Supports both stdio (default) and HTTP bridge modes.

## Installation

### Prerequisites

- Python 3.10 or higher
- `recursor` platform installed

```bash
pip install recursor
```

## Usage

### Running the Server (stdio)

The default mode for most MCP clients (like Claude Desktop).

```bash
python3 -m recursor.mcp
```

### Running the HTTP Bridge

Useful for clients that prefer HTTP over stdio.

```bash
python3 -m recursor.mcp --http
```

### Configuration

Set the following environment variables:

- `RECURSOR_API_KEY`: Your Recursor API key.
- `RECURSOR_PROJECT_ID`: The project ID to associate with tool calls.
- `RECURSOR_API_URL`: (Optional) Custom API URL.

## Available Tools

### `search_memory`
Search Recursor's memory for relevant coding patterns, past corrections, or guidelines.

### `add_correction`
Record a correction or improvement to the system's memory based on user feedback.

### `check_safety`
Validate a code snippet against safety guardrails.
