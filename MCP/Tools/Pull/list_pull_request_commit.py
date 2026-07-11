from fastmcp import FastMCP
from MCP.github_client import github_get

from MCP.server import mcp


@mcp.tool
def list_pull_request_commits(
    username: str,
    repo_name: str,
    pull_request_number: int,
):
    """List commits in a pull request."""

    if pull_request_number <= 0:
        raise ValueError("pull_request_number must be greater than 0.")

    try:
        commits = github_get(
            f"/repos/{username}/{repo_name}/pulls/{pull_request_number}/commits"
        )

        return [
            {
                "sha": commit["sha"],
                "message": commit["commit"]["message"],
                "author": commit["commit"]["author"]["name"],
                "date": commit["commit"]["author"]["date"],
                "url": commit["html_url"],
            }
            for commit in commits
        ]

    except Exception as e:
        raise RuntimeError(f"Failed to list commits for pull request #{pull_request_number}: {e}") from e