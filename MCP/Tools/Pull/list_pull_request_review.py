from fastmcp import FastMCP
from MCP.github_client import github_get

from MCP.server import mcp

from helper import get_authenticated_username


@mcp.tool
def list_pull_request_reviews(
    username: str,
    repo_name: str,
    pull_request_number: int,
):
    """List reviews on a pull request."""

    if not username:
        username = get_authenticated_username()

    if pull_request_number <= 0:
        raise ValueError("pull_request_number must be greater than 0.")

    try:
        reviews = github_get(
            f"/repos/{username}/{repo_name}/pulls/{pull_request_number}/reviews"
        )

        return [
            {
                "reviewer": review["user"]["login"],
                "state": review["state"],
                "comment": review["body"],
                "submitted_at": review["submitted_at"],
            }
            for review in reviews
        ]

    except Exception as e:
        raise RuntimeError(f"Failed to list reviews for pull request #{pull_request_number}: {e}") from e