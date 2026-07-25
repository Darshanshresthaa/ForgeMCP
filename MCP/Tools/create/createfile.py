from fastmcp import FastMCP
from MCP.github_client import github_put
import base64
from MCP.server import mcp
from MCP.helper import get_authenticated_username


@mcp.tool
def create_file(username: str,
                repo_name: str,
                path: str,
                content: str,
                message: str,
                branch: str = "main"):
    """
    Create a new file in a GitHub repository.
    
    Create/add ONE new file directly in a GitHub repo via API. For uploading an entire local folder, use push_local_to_github.
    """

    if not username:
        username = get_authenticated_username()
    

    encoded_content = base64.b64encode(
        content.encode("utf-8")
    ).decode("utf-8")


    endpoint = f"/repos/{username}/{repo_name}/contents/{path}"


    payload = {
        "message": message,
        "content": encoded_content,
        "branch": branch
    }


    try:
        response = github_put(
            endpoint,
            json=payload
        )

        return {
            "status": "success",
            "file": path,
            "branch": branch,
            "commit_sha": response["commit"]["sha"],
            "url": response["content"]["html_url"]
        }


    except Exception as e:
        raise RuntimeError(f"Failed to create file '{path}': {e}") from e