from fastmcp import FastMCP
from MCP.github_client import github_get

from MCP.server import mcp

@mcp.tool
def get_pull_request(
    username: str,
    repo_name: str,
    pull_request_number: int,
):
    """
    Retrieve detailed information about a specific pull request.
    """

    try:
        url = f"/repos/{username}/{repo_name}/pulls/{pull_request_number}"

        pr = github_get(url)

        return {
            "status": "success",
            "number": pr["number"],
            "title": pr["title"],
            "body": pr["body"],
            "state": pr["state"],
            "draft": pr["draft"],
            "author": pr["user"]["login"],
            "created_at": pr["created_at"],
            "updated_at": pr["updated_at"],
            "head_branch": pr["head"]["ref"],
            "base_branch": pr["base"]["ref"],
            "mergeable": pr.get("mergeable"),
            "mergeable_state": pr.get("mergeable_state"),
            "commits": pr["commits"],
            "changed_files": pr["changed_files"],
            "additions": pr["additions"],
            "deletions": pr["deletions"],
            "url": pr["html_url"],
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }