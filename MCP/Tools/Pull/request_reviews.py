from fastmcp import FastMCP
from MCP.github_client import github_post

from MCP.server import mcp


@mcp.tool
def request_reviewers(
    username: str,
    repo_name: str,
    pull_request_number: int,
    reviewers: list[str],
):
    """Request reviewers for a pull request."""

    if pull_request_number <= 0:
        raise ValueError("pull_request_number must be greater than 0.")

    if not reviewers:
        raise ValueError("At least one reviewer is required.")

    try:
        response = github_post(
            f"/repos/{username}/{repo_name}/pulls/{pull_request_number}/requested_reviewers",
            json={
                "reviewers": reviewers
            },
        )

        return {
            "status": "success",
            "pull_request": response["number"],
            "requested_reviewers": [
                reviewer["login"]
                for reviewer in response["requested_reviewers"]
            ],
        }

    except Exception as e:
        raise RuntimeError(f"Failed to request reviewers for pull request #{pull_request_number}: {e}") from e
