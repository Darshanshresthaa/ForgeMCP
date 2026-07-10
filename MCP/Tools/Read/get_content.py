from fastmcp import FastMCP
from MCP.github_client import github_get
import base64

from MCP.server import mcp

@mcp.tool
def get_repository_code(username: str,repo_name: str,folder_path: str = None,branch: str = "main"):
    """
    Get code files from a GitHub repository.
    Optionally filter by folder path.
    """

    try:
        # Get repository tree
        tree_response = github_get(
            f"/repos/{username}/{repo_name}/git/trees/{branch}",
            params={
                "recursive": "1"
            }
        )

        files = tree_response.get("tree", [])

        repository_code = []

        for file in files:

            # Ignore folders
            if file["type"] != "blob":
                continue

            path = file["path"]


            # If folder_path is provided,
            # only include files inside that folder
            if folder_path:
                if not path.startswith(folder_path + "/"):
                    continue


            # Get file content
            file_response = github_get(
                f"/repos/{username}/{repo_name}/contents/{path}",
                params={
                    "ref": branch
                }
            )

            content = file_response.get("content")


            if content:
                try:
                    content = base64.b64decode(
                        content
                    ).decode(
                        "utf-8",
                        errors="ignore"
                    )

                except Exception:
                    continue


            repository_code.append(
                {
                    "file": path,
                    "size": file.get("size"),
                    "code": content
                }
            )


        return {
            "repository": f"{username}/{repo_name}",
            "branch": branch,
            "folder": folder_path if folder_path else "entire repository",
            "files_count": len(repository_code),
            "files": repository_code
        }


    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }