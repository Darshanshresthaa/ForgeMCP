from fastmcp import FastMCP
from MCP.github_client import github_get

from MCP.server import mcp

@mcp.tool
def get_commit(username: str,repo_name: str,sha: str):
    """Get commit details."""

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