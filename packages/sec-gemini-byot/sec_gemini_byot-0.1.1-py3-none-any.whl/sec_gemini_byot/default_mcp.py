"""Default MCP for the BYOT client.

This allows basic file operations and shell commands."""

from fastmcp import FastMCP
from fastmcp.tools.tool import ToolAnnotations
from typing import Literal
import requests
import subprocess
import pathlib

mcp = FastMCP("BringYourOwnToolMcp")

@mcp.tool(task=True, annotations=ToolAnnotations(destructiveHint=True))
async def shell_async(command: str) -> dict[str, str | bool]:
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    return {
        "stdout": result.stdout,
        "is_error": result.returncode != 0,
        "stderr": result.stderr
    }

@mcp.tool(annotations={"destructiveHint": False, "readOnlyHint": True})
def list_files(path: str) -> list[str]:
    return [str(p) for p in pathlib.Path(path).iterdir()][:100]

@mcp.tool(annotations={"destructiveHint": False, "readOnlyHint": True})
def read_file(path: str) -> str:
    return pathlib.Path(path).read_text()

@mcp.tool(annotations={"destructiveHint": True, "readOnlyHint": False})
def write_file(path: str, content: str) -> None:
    pathlib.Path(path).write_text(content)

@mcp.tool(annotations={"destructiveHint": True, "readOnlyHint": False})
def remove_file(path: str) -> None:
    pathlib.Path(path).unlink()

@mcp.tool(annotations={"destructiveHint": True, "readOnlyHint": False})
async def remove_directory(path: str) -> None:
    pathlib.Path(path).rmdir()

@mcp.tool(annotations={"destructiveHint": True, "readOnlyHint": False, "openWorldHint": True})
async def fetch(method: Literal['GET', 'POST', 'PUT', 'DELETE', 'PATCH'], url: str) -> bytes:
    response = requests.request(method, url)
    return {
        "content": response.content,
        "status_code": response.status_code
    }