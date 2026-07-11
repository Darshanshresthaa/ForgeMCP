from fastmcp import FastMCP
from MCP.github_client import github_put

from MCP.server import mcp


@mcp.tool
def merge_pull_request(
    username: str,
    repo_name: str,
    pull_request_number: int,
    commit_title: str = "",
    commit_message: str = "",
    merge_method: str = "merge",
):
    """
    Merge a pull request.
    merge_method: merge, squash, or rebase
    """

    if pull_request_number <= 0:
        raise ValueError("pull_request_number must be greater than 0.")

    if merge_method not in {"merge", "squash", "rebase"}:
        raise ValueError("merge_method must be 'merge', 'squash', or 'rebase'.")

    payload = {"merge_method": merge_method}

    if commit_title:
        payload["commit_title"] = commit_title

    if commit_message:
        payload["commit_message"] = commit_message

    try:
        result = github_put(
            f"/repos/{username}/{repo_name}/pulls/{pull_request_number}/merge",
            json=payload,
        )

        return {
            "status": "success",
            "merged": result.get("merged", False),
            "message": result.get("message"),
            "sha": result.get("sha"),
        }

    except Exception as e:
        raise RuntimeError(f"Failed to merge pull request #{pull_request_number}: {e}") from e
