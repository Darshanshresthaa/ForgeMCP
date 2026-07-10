from fastmcp import FastMCP
from MCP.github_client import github_put
import base64


mcp = FastMCP("ForgeMCP")



@mcp.tool
def create_repository(
    repo_name: str,
    description: str = "",
    private: bool = True,
    auto_init: bool = True,
):
    """
    Create a new GitHub repository.
    """

    payload = {
        "name": repo_name,
        "description": description,
        "private": private,
        "auto_init": auto_init,
    }

    try:
        response = github_post(
            "/user/repos",
            json=payload
        )

        return {
            "status": "success",
            "name": response["name"],
            "full_name": response["full_name"],
            "private": response["private"],
            "default_branch": response["default_branch"],
            "url": response["html_url"],
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }