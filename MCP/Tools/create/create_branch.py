from fastmcp import FastMCP
from MCP.github_client import github_post,github_get
import base64
from MCP.server import mcp

from uuid import uuid4

@mcp.tool
def create_branch(
    repo_name: str,
    branch_name : str | None = None,
    source_branch: str='main',
    username: str |None = None
    ):

    """  Create a new branch from an existing branch. on existing repo"""


    if  branch_name is None:
        branch_name = f"branch-{uuid4().hex[:5]}"


    try:

        ref = github_get(
                f"/repos/{username}/{repo_name}/git/refs/heads/{source_branch}"
            )
        sha=ref['object']['sha']

        response = github_post(
            f"/repos/{username}/{repo_name}/git/refs",
            json={
                'ref':f"refs/heads/{branch_name}",
                'sha':sha
            }
        )

        return {
            "status": "success",
            "message": f"Branch '{branch_name}' created successfully.",

            "repository": repo_name,
            "owner": username,

            "branch": branch_name,
            "source_branch": source_branch,

            "ref": response["ref"],
            "commit_sha": response["object"]["sha"],

            "github_url": f"https://github.com/{username}/{repo_name}/tree/{branch_name}",
            "api_url": response["url"],
        }


    except Exception as ex:
        raise RuntimeError(
            f"Failed to create branch :{branch_name}: \n\n Reason : {str(ex)} "
        )