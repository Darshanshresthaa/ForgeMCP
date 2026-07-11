from fastmcp import FastMCP
from MCP.github_client import github_post

from MCP.server import mcp


@mcp.tool
def submit_pull_request_review(
    username: str,
    repo_name: str,
    pull_request_number: int,
    event: str,
    body: str = "",
):
    """
    Submit a pull request review.
    Events:
    APPROVE
    REQUEST_CHANGES
    COMMENT
    """

    event = event.upper()

    if event not in {
        "APPROVE",
        "REQUEST_CHANGES",
        "COMMENT",
    }:
        raise ValueError(
            "event must be APPROVE, REQUEST_CHANGES, or COMMENT."
        )


    try:
        review = github_post(
            f"/repos/{username}/{repo_name}/pulls/{pull_request_number}/reviews",
            json={
                "event": event,
                "body": body,
            },
        )

        return {
            "status": "success",
            "review_id": review["id"],
            "reviewer": review["user"]["login"],
            "state": review["state"],
            "submitted_at": review["submitted_at"],
        }

    except Exception as e:
        raise RuntimeError(f"Failed to submit review for pull request #{pull_request_number}: {e}") from e