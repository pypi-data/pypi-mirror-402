"""
KaggleRun MCP Server - Model Context Protocol server for AI agents.

This allows AI assistants like Claude Code to execute Python on Kaggle GPUs
as a native tool, without writing Python scripts.

Usage:
    # In Claude Code MCP settings, add:
    {
        "mcpServers": {
            "kagglerun": {
                "command": "python",
                "args": ["-m", "kagglerun.mcp_server"],
                "env": {
                    "KAGGLE_JUPYTER_URL": "your-url-here"
                }
            }
        }
    }
"""

import os
import sys
import json
import asyncio
from typing import Any, Sequence

try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import (
        Tool,
        TextContent,
        CallToolResult,
    )
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False

from .executor import KaggleExecutor


# Tool definitions
TOOLS = [
    {
        "name": "execute_python",
        "description": "Execute Python code on Kaggle's free GPU (T4, P100, or other available). Returns stdout/stderr and execution status. Use for ML training, data processing, or any GPU-intensive tasks.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "Python code to execute on the remote GPU kernel"
                },
                "timeout": {
                    "type": "integer",
                    "description": "Execution timeout in seconds (default: 120)",
                    "default": 120
                }
            },
            "required": ["code"]
        }
    },
    {
        "name": "get_gpu_info",
        "description": "Get information about the available GPU (model, memory, driver version)",
        "inputSchema": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "get_system_info",
        "description": "Get system information (Python version, platform, PyTorch/CUDA status)",
        "inputSchema": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "list_files",
        "description": "List files in /kaggle/working/ directory",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Directory path (default: /kaggle/working/)",
                    "default": "/kaggle/working/"
                }
            }
        }
    },
    {
        "name": "read_file",
        "description": "Read contents of a text file from the remote kernel",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "File path (relative to /kaggle/working/ or absolute)"
                }
            },
            "required": ["path"]
        }
    },
    {
        "name": "save_file",
        "description": "Save text content to a file in /kaggle/working/",
        "inputSchema": {
            "type": "object",
            "properties": {
                "filename": {
                    "type": "string",
                    "description": "Filename to create in /kaggle/working/"
                },
                "content": {
                    "type": "string",
                    "description": "Text content to save"
                }
            },
            "required": ["filename", "content"]
        }
    },
    {
        "name": "download_file",
        "description": "Download a file from /kaggle/working/ and return as base64",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "File path to download"
                }
            },
            "required": ["path"]
        }
    },
    {
        "name": "test_connection",
        "description": "Test connection to the Kaggle Jupyter kernel",
        "inputSchema": {
            "type": "object",
            "properties": {}
        }
    }
]


def get_executor() -> KaggleExecutor:
    """Get configured KaggleExecutor from environment."""
    url = os.environ.get('KAGGLE_JUPYTER_URL')
    if not url:
        raise ValueError(
            "KAGGLE_JUPYTER_URL environment variable not set. "
            "Set it to your Kaggle Jupyter proxy URL."
        )

    if not url.endswith('/proxy'):
        url = url.rstrip('/') + '/proxy'

    return KaggleExecutor(url, verbose=False)


async def handle_tool_call(name: str, arguments: dict) -> str:
    """Handle a tool call and return result."""
    try:
        executor = get_executor()

        if name == "execute_python":
            code = arguments.get("code", "")
            timeout = arguments.get("timeout", 120)
            result = executor.execute(code, timeout=timeout)

            output = result.get("output_text", "")
            errors = result.get("errors", [])
            success = result.get("success", False)
            exec_time = result.get("execution_time", 0)

            response = f"Success: {success}\n"
            response += f"Execution time: {exec_time:.2f}s\n\n"
            if output:
                response += f"Output:\n{output}\n"
            if errors:
                response += f"\nErrors:\n" + "\n".join(errors)
            return response

        elif name == "get_gpu_info":
            result = executor.get_gpu_info()
            return result.get("output_text", "No GPU info available")

        elif name == "get_system_info":
            result = executor.get_system_info()
            return result.get("output_text", "No system info available")

        elif name == "list_files":
            path = arguments.get("path", "/kaggle/working/")
            result = executor.list_files(path)
            return result.get("output_text", "Failed to list files")

        elif name == "read_file":
            path = arguments["path"]
            result = executor.read_file(path)
            if result["success"]:
                return result.get("output_text", "")
            return f"Failed to read file: {result.get('errors', ['Unknown error'])}"

        elif name == "save_file":
            filename = arguments["filename"]
            content = arguments["content"]
            result = executor.save_text(filename, content)
            if result["success"]:
                return f"Saved: /kaggle/working/{filename}"
            return f"Failed to save file: {result.get('errors', ['Unknown error'])}"

        elif name == "download_file":
            import base64
            path = arguments["path"]
            data = executor.download_file(path)
            if data:
                b64 = base64.b64encode(data).decode()
                return f"File downloaded ({len(data)} bytes). Base64:\n{b64[:500]}{'...' if len(b64) > 500 else ''}"
            return "Failed to download file"

        elif name == "test_connection":
            if executor.test_connection():
                return "Connection successful! Kaggle kernel is accessible."
            return "Connection failed. Check your URL and ensure the notebook is running."

        else:
            return f"Unknown tool: {name}"

    except Exception as e:
        return f"Error: {str(e)}"


def run_server():
    """Run the MCP server."""
    if not MCP_AVAILABLE:
        print("Error: MCP package not installed.", file=sys.stderr)
        print("Install with: pip install mcp", file=sys.stderr)
        sys.exit(1)

    server = Server("kagglerun")

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        return [
            Tool(
                name=tool["name"],
                description=tool["description"],
                inputSchema=tool["inputSchema"]
            )
            for tool in TOOLS
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict) -> Sequence[TextContent]:
        result = await handle_tool_call(name, arguments)
        return [TextContent(type="text", text=result)]

    async def main():
        async with stdio_server() as (read_stream, write_stream):
            await server.run(read_stream, write_stream)

    asyncio.run(main())


if __name__ == "__main__":
    run_server()
