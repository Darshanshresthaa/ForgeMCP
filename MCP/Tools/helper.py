from MCP.github_client import github_get

def get_authenticated_username() -> str:
    user = github_get("/user")
    return user["login"]
