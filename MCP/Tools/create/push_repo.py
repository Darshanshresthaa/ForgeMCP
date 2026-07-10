from fastmcp import FastMCP
import subprocess
import os
from MCP.server import mcp
from MCP.github_client import github_get, github_post
from MCP.config import GITHUB_TOKEN


def _run(cmd, cwd):
    """Run a git command and raise with stderr on failure."""
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError((result.stderr or result.stdout).strip())
    return result.stdout.strip()


@mcp.tool
def push_local_to_github(
    local_path: str,
    repo_name: str,
    username: str,
    commit_message: str = "Initial commit",
    branch: str = "main",
    private: bool = True,
    description: str = "",
):
    """
    Push a local folder to GitHub.

    If the repository doesn't exist yet under the authenticated account,
    it's created first. Then git is initialized locally if needed,
    all files are committed, and the folder is pushed to the branch.
    """

    if not GITHUB_TOKEN:
        return {"status": "error", "message": "GITHUB_TOKEN is not set in .env"}

    if not os.path.isdir(local_path):
        return {"status": "error", "message": f"Local path not found: {local_path}"}

    repo_existed = True
    try:
        github_get(f"/repos/{username}/{repo_name}")
    except ValueError:
        repo_existed = False
    except Exception as e:
        return {"status": "error", "message": f"Failed to check repository: {e}"}

    if not repo_existed:
        try:
            github_post(
                "/user/repos",
                json={
                    "name": repo_name,
                    "description": description,
                    "private": private,
                    "auto_init": False,
                },
            )
        except Exception as e:
            return {"status": "error", "message": f"Failed to create repository: {e}"}

    remote_url = f"https://github.com/{username}/{repo_name}.git"
  
    auth_header = f"AUTHORIZATION: bearer {GITHUB_TOKEN}"

    try:
        if not os.path.isdir(os.path.join(local_path, ".git")):
            _run(["git", "init"], cwd=local_path)
            _run(["git", "checkout", "-b", branch], cwd=local_path)

        remotes = _run(["git", "remote"], cwd=local_path).split()
        if "origin" in remotes:
            _run(["git", "remote", "set-url", "origin", remote_url], cwd=local_path)
        else:
            _run(["git", "remote", "add", "origin", remote_url], cwd=local_path)

        _run(["git", "add", "-A"], cwd=local_path)
        status = _run(["git", "status", "--porcelain"], cwd=local_path)
        if status:
            _run(["git", "commit", "-m", commit_message], cwd=local_path)

        _run(
            [
                "git", "-c", f"http.extraheader={auth_header}",
                "push", "-u", "origin", branch,
            ],
            cwd=local_path,
        )

    except RuntimeError as e:
        return {"status": "error", "message": str(e)}

    return {
        "status": "success",
        "repository_created": not repo_existed,
        "repository": f"{username}/{repo_name}",
        "branch": branch,
        "committed": bool(status),
        "url": f"https://github.com/{username}/{repo_name}",
    }
