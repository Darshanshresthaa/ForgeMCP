from fastmcp import FastMCP
from MCP.github_client import github_get
from MCP.server import mcp

@mcp.tool
def list_releases(username: str, repo_name: str, limit: int = 10):
    """List repository releases."""

    try:
        releases = github_get(
            f"/repos/{username}/{repo_name}/releases",
            params={"per_page": limit},
        )

        if not releases:
            return {
                "message": "No releases found for this repository."
            }

        result = []

        for release in releases:
            result.append({
                "name": release.get("name") or "No release name",
                "tag": release.get("tag_name") or "No tag",
                "published_at": release.get("published_at") or "Not available",
                "url": release.get("html_url") or "Not available",
            })

        return result

    except Exception as ex:
        raise RuntimeError(f"Failed to list releases: {ex}")