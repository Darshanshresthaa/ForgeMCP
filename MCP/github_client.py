import requests

from MCP.config import GITHUB_API,HEADERS
def github_get(endpoint: str, params=None):
    try:

        response = requests.get(
            f"{GITHUB_API}{endpoint}",
            headers=HEADERS,
            params=params,
            timeout=10
        )

        if response.status_code == 404:
            raise ValueError("Resource not found.")

        response.raise_for_status()

        return response.json()

    except requests.exceptions.RequestException as e:
        raise RuntimeError(e)




def github_put(endpoint: str, json: dict):
    """
    Send PUT request to GitHub API.
    """

    url = f"{GITHUB_API}{endpoint}"


    headers = {
        "Authorization": f"Bearer {HEADERS}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }


    response = requests.put(
        url,
        headers=headers,
        json=json
    )


    if response.status_code not in [200, 201]:
        raise Exception(
            f"GitHub API Error {response.status_code}: {response.text}"
        )


    return response.json()

def github_post(endpoint: str, json: dict):
    """
    Send PUT request to GitHub API.
    """

    url = f"{GITHUB_API}{endpoint}"


    headers = {
        "Authorization": f"Bearer {HEADERS}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }


    response = requests.post(
        url,
        headers=headers,
        json=json
    )


    if response.status_code not in [200, 201]:
        raise Exception(
            f"GitHub API Error {response.status_code}: {response.text}"
        )


    return response.json()


def git_delete(endpoint: str):

    url = f"{GITHUB_API_URL}{endpoint}"

    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    response = requests.delete(
        url,
        headers=headers,
    )

    if response.status_code != 204:
        raise Exception(
            f"GitHub API Error {response.status_code}: {response.text}"
        )

    return {"status": "success"}