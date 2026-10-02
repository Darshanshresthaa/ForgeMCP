from MCP.github_client import github_get
from MCP.server import mcp
from MCP.helper import get_authenticated_username


@mcp.tool
def list_issues(
    repo_name: str,
    state: str = "open",
    labels: str | None = None,
    limit: int = 10,
    page: int = 1,
    username: str | None = None,
):
    """List issues of a repo (pull requests excluded). labels: comma-separated label names."""

    if state not in {"open", "closed", "all"}:
        raise ValueError("state must be 'open', 'closed', or 'all'.")

    if not 1 <= limit <= 100:
        raise ValueError("limit must be between 1 and 100.")

    if page < 1:
        raise ValueError("page must be greater than 0.")

    if username is None:
        username = get_authenticated_username()

    params = {"state": state, "per_page": limit, "page": page}

    if labels:
        params["labels"] = labels

    try:
        issues = github_get(
            f"/repos/{username}/{repo_name}/issues",
            params=params,
        )

        # GitHub returns pull requests in this endpoint too; skip them.
        return [
            {
                "number": issue["number"],
                "title": issue["title"],
                "state": issue["state"],
                "author": issue["user"]["login"],
                "labels": [label["name"] for label in issue.get("labels", [])],
                "comments": issue["comments"],
                "created_at": issue["created_at"],
                "url": issue["html_url"],
            }
            for issue in issues
            if "pull_request" not in issue
        ]

    except ValueError:
        raise

    except Exception as e:
        raise RuntimeError(f"Failed to list issues: {e}") from e
