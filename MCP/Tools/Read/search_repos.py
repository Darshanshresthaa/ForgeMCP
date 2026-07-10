from fastmcp import FastMCP
from MCP.github_client import github_get

from MCP.server import mcp
@mcp.tool
def search_repos(query: str,limit:int=10):
    """Search GitHub users by username or keyword."""

    try:
        users = github_get(
            "/search/repositories",
            params={"q": query,
                   'per_page':limit}
        )

        return users["items"]

    except ValueError:
        raise

    except Exception as e:
        raise RuntimeError(
            f"Failed to search users for '{query}'."
        ) from e