from fastmcp import FastMCP
from MCP.github_client import github_get

from MCP.server import mcp


@mcp.tool
def get_langauge(username:str,repo_name:str):

    try:
        languages = github_get(f"/repos/{username}/{repo_name}/languages")

        return languages

    except ValueError:
        raise

    except Exception as ex:
        raise RuntimeError(f"Failed to get README: {ex}")

