from fastmcp import FastMCP
from MCP.github_client import github_get

from MCP.server import mcp

@mcp.tool
def list_pull_requests(
    username: str,
    repo_name: str,
    state: str = "open",
    base: str | None = None,
    sort: str = "created",
    direction: str = "desc",
):
    """
    List pull requests in a GitHub repository.
    """

    if state not in {"open", "closed", "all"}:
        raise ValueError("state must be 'open', 'closed', or 'all'.")

    params = {
        "state": state,
        "sort": sort,
        "direction": direction,
    }

    if base:
        params["base"] = base

    pulls = github_get(
        f"/repos/{username}/{repo_name}/pulls",
        params=params,
    )

    result = []

    for pr in pulls:
        result.append(
            {
                "number": pr["number"],
                "title": pr["title"],
                "state": pr["state"],
                "author": pr["user"]["login"],
                "source_branch": pr["head"]["ref"],
                "target_branch": pr["base"]["ref"],
                "draft": pr["draft"],
                "mergeable": pr.get("mergeable"),
                "created_at": pr["created_at"],
                "updated_at": pr["updated_at"],
                "url": pr["html_url"],
            }
        )

    return result