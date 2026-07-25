from fastmcp import FastMCP
from MCP.github_client import github_get

from MCP.server import mcp

from MCP.helper import get_authenticated_username


@mcp.tool
def get_latest_release(username: str,
                        repo_name: str
                    ):
    
    """Get the newest published release of a repo. Use list_releases for full release history."""

    if not username:
        username = get_authenticated_username()
        
    try:
        release = github_get(
            f"/repos/{username}/{repo_name}/releases/latest"
        )

        return {
            "name": release.get("name") or "No release name",
            "tag": release.get("tag_name") or "No tag",
            "published_at": release.get("published_at") or "Not available",
            "url": release.get("html_url") or "Not available",
        }

    except ValueError:
        return {
            "message": "No published release found for this repository."
        }

    except Exception as ex:
        raise RuntimeError(f"Failed to get latest release: {ex}")