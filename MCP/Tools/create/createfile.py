from fastmcp import FastMCP
from MCP.github_client import github_put
import base64


mcp = FastMCP("ForgeMCP")


@mcp.tool
def create_file(username: str,repo_name: str,path: str,content: str,message: str,branch: str = "main"):
    """
    Create a new file in a GitHub repository.
    """
    

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
        return {
            "status": "error",
            "message": str(e)
        }