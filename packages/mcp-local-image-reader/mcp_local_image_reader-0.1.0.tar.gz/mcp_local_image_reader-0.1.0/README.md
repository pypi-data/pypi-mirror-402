# MCP Image Reader

[![PyPI version](https://badge.fury.io/py/mcp-local-image-reader.svg)](https://badge.fury.io/py/mcp-local-image-reader)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A simple [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) server that reads local images and returns them as `ImageContent` for LLM vision analysis.

<a href="vscode:mcp/install?%7B%22name%22%3A%22local-image-reader%22%2C%22command%22%3A%22uvx%22%2C%22args%22%3A%5B%22mcp-local-image-reader%22%5D%7D"><img src="https://img.shields.io/badge/VS_Code-Install_Server-0098FF?style=for-the-badge&logo=visualstudiocode&logoColor=white" alt="Install in VS Code"></a>

## Features

- 📷 Read local images and return as base64-encoded `ImageContent`
- 🔧 Single tool: `read_image` - simple and focused
- 🚀 One-click installation for VS Code
- 📦 Install via PyPI with `uvx` - no environment setup needed

## Supported Formats

PNG, JPEG, GIF, WebP, BMP, SVG

## Installation

### VS Code (Recommended)

Click the button above, or manually add to your VS Code settings:

**For a specific version (recommended for security):**
```json
{
  "mcp": {
    "servers": {
      "local-image-reader": {
        "command": "uvx",
        "args": ["mcp-local-image-reader==0.1.0"]
      }
    }
  }
}
```

**For the latest version:**
```json
{
  "mcp": {
    "servers": {
      "local-image-reader": {
        "command": "uvx",
        "args": ["mcp-local-image-reader"]
      }
    }
  }
}
```

### Claude Desktop

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "local-image-reader": {
      "command": "uvx",
      "args": ["mcp-local-image-reader==0.1.0"]
    }
  }
}
```

## Usage

In your AI assistant, ask it to read an image:

```
Please read the image at C:\Users\me\Pictures\screenshot.png and describe what you see.
```

The assistant will use the `read_image` tool to load the image and analyze it.

## Security

### Version Pinning

For production use, always pin to a specific version:

```json
"args": ["mcp-local-image-reader==0.1.0"]
```

This ensures you won't automatically pull potentially malicious updates.

### Source Code

This project is intentionally minimal (~100 lines) for easy auditing. The entire implementation is in [`server.py`](./server.py).

## Known Issues

### ⚠️ Gemini Does Not Recognize Images from MCP

When using VS Code Copilot with Gemini models, images returned via MCP `ImageContent` are **not visually recognized**. The tool execution succeeds, but Gemini cannot "see" the image content.

| Model | MCP Image Recognition |
|-------|----------------------|
| Claude | ✅ Works |
| GPT | ✅ Works |
| Gemini | ❌ Not working |

**Root Cause:** This is a known issue with how Gemini handles non-text content types in MCP responses.

**Related Issue:** [gemini-cli #15851 - Only text content type supported](https://github.com/google-gemini/gemini-cli/issues/15851)

**Workaround:** Use Claude or GPT models for image analysis tasks until this issue is resolved.

## Tool Reference

### `read_image`

Reads an image from the filesystem and returns it as base64-encoded `ImageContent`.

**Parameters:**
- `file_path` (string, required): Absolute path to the image file

**Returns:**
- `ImageContent` with base64-encoded image data and appropriate MIME type

**Example:**
```json
{
  "name": "read_image",
  "arguments": {
    "file_path": "/path/to/image.png"
  }
}
```

## Development

```bash
# Clone the repository
git clone https://github.com/masachika-kamada/mcp-image-reader.git
cd mcp-image-reader

# Install dependencies
uv sync

# Run locally
uv run python server.py

# Test with MCP Inspector
npx @modelcontextprotocol/inspector uv run python server.py
```

## License

MIT License - see [LICENSE](./LICENSE) for details.

## Contributing

Issues and pull requests are welcome! Please feel free to contribute.

## Related Projects

- [moiri-gamboni/image-reader-mcp](https://github.com/moiri-gamboni/image-reader-mcp) - TypeScript implementation with directory listing
- [k2sebeom/image-reader-mcp](https://github.com/k2sebeom/image-reader-mcp) - Python implementation with remote URL support and image resizing
