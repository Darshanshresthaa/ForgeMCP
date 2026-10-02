from MCP.github_client import github_post
from MCP.server import mcp
from MCP.helper import get_authenticated_username


@mcp.tool
def create_issue(
    repo_name: str,
    title: str,
    body: str = "",
    labels: list[str] | None = None,
    assignees: list[str] | None = None,
    username: str | None = None,
):
    """Create a new issue in a GitHub repository (optional labels and assignees)."""

    if not title.strip():
        raise ValueError("title cannot be empty.")

    if username is None:
        username = get_authenticated_username()

    payload = {"title": title, "body": body}

    if labels:
        payload["labels"] = labels

    if assignees:
        payload["assignees"] = assignees

    try:
        issue = github_post(
            f"/repos/{username}/{repo_name}/issues",
            json=payload,
        )

        return {
            "status": "success",
            "number": issue["number"],
            "title": issue["title"],
            "state": issue["state"],
            "labels": [label["name"] for label in issue.get("labels", [])],
            "url": issue["html_url"],
        }

    except Exception as e:
        raise RuntimeError(f"Failed to create issue '{title}': {e}") from e
