from fastmcp import FastMCP
from MCP.github_client import github_get

from MCP.server import mcp

from MCP.helper import get_authenticated_username

@mcp.tool
def get_commit(
    repo_name: str,
    sha: str,
    username: str | None = None
    ):
    
    """Get commit details."""


    if  username in None:
        username = get_authenticated_username()

    try:
        commit = github_get(
            f"/repos/{username}/{repo_name}/commits/{sha}"
        )

        return {
            "sha": commit["sha"],
            "message": commit["commit"]["message"],
            "author": commit["commit"]["author"]["name"],
            "date": commit["commit"]["author"]["date"],
            "files_changed": [
                {
                    "filename": file["filename"],
                    "status": file["status"],
                    "changes": file["changes"],
                }
                for file in commit.get("files", [])
            ],
            "url": commit["html_url"],
        }

    except Exception as e:
        raise RuntimeError(f"Failed to get commit: {e}")