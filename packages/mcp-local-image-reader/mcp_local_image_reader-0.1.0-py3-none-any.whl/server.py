"""
MCP Image Reader Server
A simple MCP server that reads local images and returns them as ImageContent.
"""

import asyncio
import base64
import mimetypes
from pathlib import Path

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    TextContent,
    ImageContent,
    Tool,
)

__version__ = "0.1.0"

server = Server("image-reader")


def get_media_type(file_path: str) -> str:
    """Get media type from file path."""
    mime_type, _ = mimetypes.guess_type(file_path)
    return mime_type or "application/octet-stream"


def read_image_as_base64(file_path: str) -> tuple[str, str]:
    """Read image and return as base64 encoded string."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    if not path.is_file():
        raise ValueError(f"Not a file: {file_path}")

    media_type = get_media_type(file_path)

    with open(path, "rb") as f:
        data = base64.standard_b64encode(f.read()).decode("utf-8")

    return data, media_type


@server.list_tools()
async def list_tools() -> list[Tool]:
    """Return list of available tools."""
    return [
        Tool(
            name="read_image",
            description="Read an image from the filesystem and return it as base64-encoded ImageContent. Supported formats: PNG, JPEG, GIF, WebP",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Absolute path to the image file"
                    }
                },
                "required": ["file_path"]
            }
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent | ImageContent]:
    """Execute tool."""

    if name == "read_image":
        file_path = arguments.get("file_path")
        if not file_path:
            return [TextContent(type="text", text="Error: file_path is required")]

        try:
            data, media_type = read_image_as_base64(file_path)

            return [
                ImageContent(
                    type="image",
                    data=data,
                    mimeType=media_type
                )
            ]
        except FileNotFoundError as e:
            return [TextContent(type="text", text=f"Error: {e}")]
        except Exception as e:
            return [TextContent(type="text", text=f"Error reading image: {e}")]

    return [TextContent(type="text", text=f"Unknown tool: {name}")]


async def run_server():
    """Run the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


def main():
    """Main entry point."""
    asyncio.run(run_server())


if __name__ == "__main__":
    main()
