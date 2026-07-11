from fastmcp import FastMCP
from MCP.github_client import github_get

from MCP.server import mcp


@mcp.tool
def list_pull_request_files(
    username: str,
    repo_name: str,
    pull_request_number: int,
):
    """
    List all files changed in a pull request.
    """

    if pull_request_number <= 0:
        raise ValueError("pull_request_number must be greater than 0.")

    try:
        url = f"/repos/{username}/{repo_name}/pulls/{pull_request_number}/files"

        files = github_get(url)

        return {
            "status": "success",
            "pull_request_number": pull_request_number,
            "total_files": len(files),
            "files": [
                {
                    "filename": file["filename"],
                    "status": file["status"],
                    "additions": file["additions"],
                    "deletions": file["deletions"],
                    "changes": file["changes"],
                    "blob_url": file["blob_url"],
                    "raw_url": file["raw_url"],
                    "patch": file.get("patch"),
                }
                for file in files
            ],
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
        }