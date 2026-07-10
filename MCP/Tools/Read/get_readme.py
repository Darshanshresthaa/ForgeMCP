from fastmcp import FastMCP
from MCP.github_client import github_get
import base64

from MCP.server import mcp


@mcp.tool
def get_readme(username: str, repo_name: str):
    """Get repository README."""

    try:
        readme = github_get(f"/repos/{username}/{repo_name}/readme")

        return {
            "name": readme["name"],
            "path": readme["path"],
            "url": readme["html_url"],
            "content": base64.b64decode(
                readme["content"]
            ).decode("utf-8"),
        }

    except Exception as ex:
        raise RuntimeError(f"Failed to get README: {ex}")