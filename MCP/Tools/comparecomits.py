from fastmcp import FastMCP
from MCP.github_client import github_get


mcp = FastMCP("ForgeMCP")


@mcp.tool
def compare_commits(
    username: str,
    repo_name: str,
    base: str,
    head: str,
):
    """Compare two commits or branches."""

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