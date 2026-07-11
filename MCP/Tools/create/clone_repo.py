from fastmcp import FastMCP
import subprocess
import os
from MCP.server import mcp



@mcp.tool
def clone_repository(
    repo_url: str,
    destination: str = ".",
):
    """
    Clone a GitHub repository.
    """

    try:
        repo_name = os.path.basename(repo_url.rstrip("/"))
        if repo_name.endswith(".git"):
            repo_name = repo_name[:-4]

        subprocess.run(
            ["git", "clone", repo_url],
            cwd=destination,
            check=True,
            capture_output=True,
            text=True,
        )

        return {
            "status": "success",
            "repository": repo_name,
            "location": os.path.join(destination, repo_name),
        }

    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to clone repository: {e.stderr.strip()}") from e

    except Exception as e:
        raise RuntimeError(f"Failed to clone repository: {e}") from e