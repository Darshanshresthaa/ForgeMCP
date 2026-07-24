from fastmcp import FastMCP
from MCP.github_client import github_get

from MCP.server import mcp

@mcp.tool
def list_repositories(username: str):
    """
    Returns a list of all public repositories for a GitHub user.
    """
    try:
        repos = github_get(f"/users/{username}/repos")

        repositories = []


        for repo in repos:
            repositories.append({
                "name": repo["name"],
                "full_name": repo["full_name"],
                "description": repo["description"],
                "private": repo["private"],
                "language": repo["language"],
                "default_branch": repo["default_branch"],
                "stars": repo["stargazers_count"],
                "forks": repo["forks_count"],
                "open_issues": repo["open_issues_count"],
                "watchers": repo["watchers_count"],
                "size_kb": repo["size"],
                "created_at": repo["created_at"],
                "updated_at": repo["updated_at"],
                "pushed_at": repo["pushed_at"],
                "url": repo["html_url"],
            })

        return repositories
    
    except ValueError:
        raise

    except Exception as ex:
        raise RuntimeError(
            f"Failed to fetch repositories for user '{username}': {ex}"
        )