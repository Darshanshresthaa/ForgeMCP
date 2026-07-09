import requests

from MCP.Tools.config import GITHUB_API,HEADERS
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