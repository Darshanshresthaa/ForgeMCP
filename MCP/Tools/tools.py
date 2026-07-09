from fastmcp import FastMCP
from MCP.Tools.github_client import github_get

mcp = FastMCP("ForgeMCP")

@mcp.tool
def get_profile(username: str):

    try:
        profile = github_get(f"/users/{username}")

        return profile

    except ValueError:
        raise

    except Exception as e:
        raise RuntimeError(f"Failed to fetch profile for : '{username}'.")
    