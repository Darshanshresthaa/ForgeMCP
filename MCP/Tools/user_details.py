from fastmcp import FastMCP
from MCP.github_client import github_get


mcp = FastMCP("ForgeMCP")

@mcp.tool
def get_user_details(username: str):

    """Get basic GitHub user details. which is publically available"""
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
    