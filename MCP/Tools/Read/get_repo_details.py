from fastmcp import FastMCP
from MCP.github_client import github_get
from MCP.server import mcp


@mcp.tool
def get_repository(username: str, repo_name: str):
    """
    Get repository details including metadata, statistics, and configuration.
    """

    try:
        details = github_get(f"/repos/{username}/{repo_name}")

        return {
            "name": details["name"],
            "full_name": details["full_name"],
            "description": details["description"],

            "owner": details["owner"]["login"],

            "visibility": details["visibility"],
            "private": details["private"],

            "language": details["language"],
            "topics": details["topics"],
            "license": details["license"]["name"] if details["license"] else None,

            "default_branch": details["default_branch"],

            "size_kb": details["size"],

            "stars": details["stargazers_count"],
            "watchers": details["watchers_count"],
            "forks": details["forks_count"],
            "open_issues": details["open_issues_count"],

            "has_issues": details["has_issues"],
            "has_wiki": details["has_wiki"],
            "has_projects": details["has_projects"],
            "has_discussions": details["has_discussions"],
            "has_pages": details["has_pages"],

            "created_at": details["created_at"],
            "updated_at": details["updated_at"],
            "last_push": details["pushed_at"],

            "repository_url": details["html_url"],
            "clone_url": details["clone_url"],

            "homepage": details["homepage"],

            "is_template": details["is_template"],
            "archived": details["archived"],
            "disabled": details["disabled"],
        }

    except ValueError:
        raise

    except Exception as e:
        raise RuntimeError(
            f"Failed to fetch repository '{username}/{repo_name}'."
        ) 