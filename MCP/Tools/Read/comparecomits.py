from fastmcp import FastMCP
from MCP.github_client import github_get

from MCP.server import mcp

from MCP.helper import get_authenticated_username

@mcp.tool
def compare_commits(
    repo_name: str,
    base: str,
    head: str,
    username: str | None = None
):
    """Diff two commits/branches: ahead/behind counts + commit list between base and head. For single commit info use get_commit."""

    if  username is None:
        username = get_authenticated_username()
        

    try:
        comparison = github_get(
            f"/repos/{username}/{repo_name}/compare/{base}...{head}"
        )

        return {
            "status": comparison["status"],
            "ahead_by": comparison["ahead_by"],
            "behind_by": comparison["behind_by"],
            "total_commits": comparison["total_commits"],
            "commits": [
                {
                    "sha": commit["sha"],
                    "message": commit["commit"]["message"],
                    "author": commit["commit"]["author"]["name"],
                }
                for commit in comparison["commits"]
            ],
        }

    except Exception as e:
        raise RuntimeError(f"Failed to compare commits: {e}")