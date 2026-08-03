from fastmcp import FastMCP
from MCP.github_client import github_get


from MCP.server import mcp

from MCP.helper import get_authenticated_username

@mcp.tool
def get_user_details(username: str | None = None):

    """Get basic GitHub user details. which is publically available"""


    if  username is None:
        username = get_authenticated_username()

    try:
        profile = github_get(f"/users/{username}")

        return {
            "username": profile["login"],
            "name": profile["name"],
            "bio": profile["bio"],
            "company": profile["company"],
            "location": profile["location"],
            "email": profile["email"],
            "public_repositories": profile["public_repos"],
            "followers": profile["followers"],
            "following": profile["following"],
            "profile_url": profile["html_url"],
            "created_at": profile["created_at"],
            "user_profile_type":profile['user_view_type'],
            "profile_url":profile['html_url']

        }

    except ValueError:
        raise

    except Exception as e:
        raise RuntimeError(f"Failed to fetch profile for : '{username}'.")
    