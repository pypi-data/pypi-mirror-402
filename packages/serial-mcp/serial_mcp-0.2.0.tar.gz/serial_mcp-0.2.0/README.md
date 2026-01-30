# serial-mcp

MCP server for serial port communication. Provides tools to open, read, write, and manage serial ports through the Model Context Protocol.

*Written by and for AI.*

## Features

- List available serial ports on the system
- Open ports with configurable baud rate, parity, stop bits, and flow control
- Read data by byte count, terminator character, or duration
- Write string or hex data
- Send BREAK signals
- Monitor port status and control line states

## Installation

### Via PyPI

```bash
uvx serial-mcp@latest
```

### Local Clone

```bash
git clone https://github.com/davidalo/serial-mcp.git
cd serial-mcp
uvx --from "$(pwd)" serial-mcp
```

## Integration

### Via PyPI

```bash
# Claude Code
claude mcp add serial -- uvx serial-mcp@latest

# Codex CLI
codex mcp add serial -- uvx serial-mcp@latest
```

### Local Clone

```bash
git clone https://github.com/davidalo/serial-mcp.git
cd serial-mcp

# Claude Code
claude mcp add serial -- uvx --from "$(pwd)" serial-mcp

# Codex CLI
codex mcp add serial -- uvx --from "$(pwd)" serial-mcp
```

## Tools

| Tool | Description |
|------|-------------|
| `list_ports` | List available system serial ports |
| `open_port` | Open a serial port with configuration (baud rate, parity, stop bits, etc.) |
| `close_port` | Close an open port |
| `write_data` | Write string or hex data to a port |
| `read_bytes` | Read N bytes with timeout |
| `read_until` | Read until a terminator character |
| `read_for_duration` | Read continuously for N seconds |
| `send_break` | Send a BREAK signal |
| `get_port_status` | Get port status and control line states |
| `list_open_ports` | List all currently managed ports |

## Testing with Virtual Ports

Use `socat` to create virtual serial port pairs for testing:

```bash
# Create virtual port pair
socat -d -d pty,raw,echo=0,link=/tmp/ttyV0 pty,raw,echo=0,link=/tmp/ttyV1
```

Then open `/tmp/ttyV0` with the MCP server and `/tmp/ttyV1` with another terminal program to test communication.

## Requirements

- Python 3.10+
- `uv` package manager (for running with `uvx`)

## License

MIT
