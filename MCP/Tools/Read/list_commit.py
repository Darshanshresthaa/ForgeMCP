from fastmcp import FastMCP
from MCP.github_client import github_get


mcp = FastMCP("ForgeMCP")


@mcp.tool
def list_commits(username: str,repo_name: str,limit: int = 10,page: int = 1,branch: str | None = None,author: str | None = None):
    """List commits from a GitHub repository."""

    if not username.strip():
        raise ValueError("Username cannot be empty.")

    if not repo_name.strip():
        raise ValueError("Repository name cannot be empty.")

    if not 1 <= limit <= 100:
        raise ValueError("limit must be between 1 and 100.")

    if page < 1:
        raise ValueError("page must be greater than 0.")

    try:
        params = {
            "per_page": limit,
            "page": page,
        }

        if branch:
            params["sha"] = branch

        if author:
            params["author"] = author

        commits = github_get(
            f"/repos/{username}/{repo_name}/commits",
            params=params,
        )

        return [
            {
                "sha": commit["sha"],
                "message": commit["commit"]["message"],
                "author": (
                    commit["author"]["login"]
                    if commit.get("author")
                    else commit["commit"]["author"]["name"]
                ),
                "email": commit["commit"]["author"]["email"],
                "date": commit["commit"]["author"]["date"],
                "verified": commit["commit"]["verification"]["verified"],
                "commit_url": commit["html_url"],
            }
            for commit in commits
        ]

    except ValueError:
        raise

    except Exception as e:
        raise RuntimeError(
            f"Failed to fetch commits for '{username}/{repo_name}'."
        ) from e