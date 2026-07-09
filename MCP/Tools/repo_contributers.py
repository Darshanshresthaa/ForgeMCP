from fastmcp import FastMCP
from MCP.github_client import github_get


mcp = FastMCP("ForgeMCP")



@mcp.tool
def repo_contributors(username: str, repo_name: str, limit: int = 10):
    """List repository contributors."""

    contributors = github_get(
        f"/repos/{username}/{repo_name}/contributors",
        params={"per_page": limit},
    )

    result = []

    for contributor in contributors:
        result.append({
            "username": contributor["login"],
            "contributions": contributor["contributions"],
            "profile": contributor["html_url"],
        })

    return result