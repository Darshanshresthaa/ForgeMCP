from fastmcp import FastMCP
from MCP.github_client import github_patch

from MCP.server import mcp

from helper import get_authenticated_username

@mcp.tool
def update_pull_request(
    username: str,
    repo_name: str,
    pull_request_number: int,
    title: str | None = None,
    body: str | None = None,
    state: str | None = None,
    base: str | None = None,
):
    """Update a PR's title, body, state, or base branch (partial update, only set fields provided)."""

    payload = {}

    if not username:
        username = get_authenticated_username()

    if title is not None:
        payload["title"] = title

    if body is not None:
        payload["body"] = body

    if state is not None:
        if state not in {"open", "closed"}:
            raise ValueError(
                "state must be either 'open' or 'closed'."
            )
        payload["state"] = state

    if base is not None:
        payload["base"] = base

    if not payload:
        raise ValueError("At least one field must be provided for update.")

    try:
        pr = github_patch(
            f"/repos/{username}/{repo_name}/pulls/{pull_request_number}",
            json=payload,
        )

        return {
            "status": "success",
            "number": pr["number"],
            "title": pr["title"],
            "state": pr["state"],
            "url": pr["html_url"],
            "updated_at": pr["updated_at"],
        }

    except Exception as e:
        raise RuntimeError(f"Failed to update pull request #{pull_request_number}: {e}") from e