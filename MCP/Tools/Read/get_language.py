from fastmcp import FastMCP
from MCP.github_client import github_get

from MCP.server import mcp

from helper import get_authenticated_username


@mcp.tool
def get_langauge(username:str,
                 repo_name:str
                 ):

    if not username:
        username = get_authenticated_username()
        

    try:
        languages = github_get(f"/repos/{username}/{repo_name}/languages")

        return languages

    except ValueError:
        raise

    except Exception as ex:
        raise RuntimeError(f"Failed to get README: {ex}")

