from MCP.github_client import git_delete
from MCP.server import mcp
from MCP.helper import get_authenticated_username

@mcp.tool

def unstar_git_repository(
    repo_name:str,
    user_name:str | None = None
):

    """ Remove the reposititory from star section only if availaible in star repo"""


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


            response = git_delete(
                f"/user/starred/{user_name}/{repo_name}"
            )

            return {
                "status": "success",
                "message": f"Repository unstarred successfully: {user_name}/{repo_name}",
                "repository": f"{user_name}/{repo_name}",
                "url": f"https://github.com/{user_name}/{repo_name}",
                "status_code": response.status_code,
            }

    

    except Exception as ex:
         pass
