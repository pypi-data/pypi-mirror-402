# Time Server MCP

A simple MCP (Model Control Protocol) server that provides current time functionality.

## Overview

This package implements a lightweight MCP server that exposes a `get_current_time` tool which can return the current time in any specified timezone.

## Installation

```bash
pip install time-server-mcp
```

## Dependencies

- `pytz` - For timezone handling
- `mcp` - The Model Control Protocol framework

## Usage

### Starting the Server

You can start the server using the provided command-line script:

```bash
time-server
```

### Using the Server

Once the server is running, you can interact with it using any MCP client.

#### Example: Getting Current Time

```python
from mcp.client import Client

# Connect to the time server
client = Client(transport="streamable-http")

# Get current time in default timezone
result = client.get_current_time()
print(f"Current time: {result}")

# Get current time in a specific timezone
result = client.get_current_time(timezone="Asia/Shanghai")
print(f"Current time in Shanghai: {result}")
```

## Available Tools

### `get_current_time(timezone=None)`

Returns the current time in the specified timezone.

- `timezone` (optional): A timezone string (e.g., "Asia/Shanghai", "America/New_York")
- Returns: A formatted time string ("YYYY-MM-DD HH:MM:SS.SSSSSS TIMEZONE")

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
