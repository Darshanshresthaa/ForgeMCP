from MCP.github_client import github_post
from MCP.server import mcp
from MCP.helper import get_authenticated_username


@mcp.tool
def add_issue_comment(
    repo_name: str,
    issue_number: int,
    body: str,
    username: str | None = None,
):
    """Add a comment to an issue or pull request (both use the issue number)."""

    if issue_number <= 0:
        raise ValueError("issue_number must be greater than 0.")

    if not body.strip():
        raise ValueError("body cannot be empty.")

    if username is None:
        username = get_authenticated_username()

    try:
        comment = github_post(
            f"/repos/{username}/{repo_name}/issues/{issue_number}/comments",
            json={"body": body},
        )

        return {
            "status": "success",
            "comment_id": comment["id"],
            "author": comment["user"]["login"],
            "created_at": comment["created_at"],
            "url": comment["html_url"],
        }

    except Exception as e:
        raise RuntimeError(f"Failed to comment on #{issue_number}: {e}") from e
