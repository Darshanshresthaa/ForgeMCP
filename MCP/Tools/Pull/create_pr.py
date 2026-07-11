from fastmcp import FastMCP
from MCP.github_client import github_post

from MCP.server import mcp



@mcp.tool
def create_pull_request(
    username: str,
    repo_name: str,
    title: str,
    head: str,
    base: str = "main",
    body: str = "",
    draft: bool = False,
):
    """Create a pull request."""

    if head == base:
        raise ValueError("head and base branches cannot be the same.")
    
    payload = {
        "title": title,
        "head": head,
        "base": base,
        "body": body,
        "draft": draft,
    }

    url = f"/repos/{username}/{repo_name}/pulls"

    pr = github_post(url, payload)

    return {
        "number": pr["number"],
        "title": pr["title"],
        "state": pr["state"],
        "url": pr["html_url"],
        "head": pr["head"]["ref"],
        "base": pr["base"]["ref"],
        "draft": pr["draft"],
        "created_at": pr["created_at"],
    }