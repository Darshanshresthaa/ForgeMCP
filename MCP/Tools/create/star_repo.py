from github_client import github_put
from helper import get_authenticated_username
from MCP.server import mcp


@mcp.tool
def star_repository(
    repo_name: str,
    user_name: str | None = None,
):
    """
    Star a GitHub repository.

   repo_name : repo_name or url 
    """

    try:

    
        if repo_name.startswith("https://github.com/"):


            repo_name = repo_name.replace("https://github.com/","")

            parts = repo_name.strip("/").split("/")

            if len(parts) != 2:
                raise ValueError(
                    "Invalid GitHub URL. "
                    "Expected: https://github.com/owner/repo"
                )

            user_name = parts[0]
            repo_name = parts[1]

    
        elif user_name is not None:

            repo_name = repo_name.strip("/")
            user_name = user_name.strip("/")
 
  
        else:
            user_name = get_authenticated_username()
            repo_name = repo_name.strip("/")


        response = github_put(
            f"/user/starred/{user_name}/{repo_name}"
        )

        repo_url = f"https://github.com/{user_name}/{repo_name}"

        return {
            "status": "success",
            "message": (
                f"Repository starred successfully: "
                f"{user_name}/{repo_name}"
            ),
            "repository": f"{user_name}/{repo_name}",
            "status_code":response.status_code,
            "url": repo_url,
        }

    except Exception as ex:
        raise RuntimeError(
            f"Failed to star repository "
            f"{user_name}/{repo_name}: {ex}"
        ) from ex