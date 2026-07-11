import time
import requests

from MCP.config import GITHUB_API, HEADERS, GITHUB_TOKEN

MAX_RETRIES = 3
BASE_BACKOFF_SECONDS = 1.0
MAX_RATE_LIMIT_WAIT_SECONDS = 60


def _auth_headers(extra: dict = None) -> dict:
    """Build request headers, raising early if a token-requiring call has no token."""
    if not GITHUB_TOKEN:
        raise RuntimeError(
            "GITHUB_TOKEN is not set. Add it to your .env file before calling "
            "write/delete endpoints."
        )
    headers = dict(HEADERS)
    if extra:
        headers.update(extra)
    return headers


def _request_with_retry(method: str, endpoint: str, headers: dict, params=None, json=None):
    """
    Perform an HTTP request against the GitHub API with retry/backoff for
    transient network errors, primary rate limits (403/429 with
    X-RateLimit-Remaining: 0), secondary rate limits (Retry-After), and
    transient 5xx server errors.
    """
    url = f"{GITHUB_API}{endpoint}"
    last_network_error = None

    for attempt in range(MAX_RETRIES + 1):
        try:
            response = requests.request(
                method,
                url,
                headers=headers,
                params=params,
                json=json,
                timeout=15,
            )
        except requests.exceptions.RequestException as e:
            last_network_error = e
            if attempt == MAX_RETRIES:
                raise RuntimeError(f"Network error calling GitHub API: {e}") from e
            time.sleep(BASE_BACKOFF_SECONDS * (2 ** attempt))
            continue

        if response.status_code in (403, 429):
            remaining = response.headers.get("X-RateLimit-Remaining")
            retry_after = response.headers.get("Retry-After")

            # Primary rate limit exhausted
            if remaining == "0":
                reset_ts = response.headers.get("X-RateLimit-Reset")
                wait_seconds = BASE_BACKOFF_SECONDS * (2 ** attempt)
                if reset_ts:
                    wait_seconds = max(0, int(reset_ts) - int(time.time())) + 1

                if attempt == MAX_RETRIES or wait_seconds > MAX_RATE_LIMIT_WAIT_SECONDS:
                    raise RuntimeError(
                        "GitHub API rate limit exceeded. "
                        f"Resets in ~{max(0, wait_seconds)}s."
                    )
                time.sleep(wait_seconds)
                continue

            # Secondary rate limit (abuse detection)
            if retry_after:
                wait_seconds = min(float(retry_after), MAX_RATE_LIMIT_WAIT_SECONDS)
                if attempt == MAX_RETRIES:
                    raise RuntimeError("GitHub API secondary rate limit exceeded.")
                time.sleep(wait_seconds)
                continue

        # Transient server-side errors: retry
        if response.status_code in (500, 502, 503, 504):
            if attempt < MAX_RETRIES:
                time.sleep(BASE_BACKOFF_SECONDS * (2 ** attempt))
                continue

        return response

    # Only reached if every attempt hit a network error and MAX_RETRIES == 0
    raise RuntimeError(f"Network error calling GitHub API: {last_network_error}")


def github_get(endpoint: str, params=None):
    response = _request_with_retry("GET", endpoint, headers=HEADERS, params=params)

    if response.status_code == 404:
        raise ValueError("Resource not found.")

    if not response.ok:
        raise RuntimeError(f"GitHub API Error {response.status_code}: {response.text}")

    return response.json()


def github_put(endpoint: str, json: dict):
    """Send PUT request to GitHub API."""
    headers = _auth_headers()
    response = _request_with_retry("PUT", endpoint, headers=headers, json=json)

    if response.status_code == 404:
        raise ValueError("Resource not found.")

    if response.status_code not in (200, 201):
        raise RuntimeError(f"GitHub API Error {response.status_code}: {response.text}")

    return response.json()


def github_post(endpoint: str, json: dict):
    """Send POST request to GitHub API."""
    headers = _auth_headers()
    response = _request_with_retry("POST", endpoint, headers=headers, json=json)

    if response.status_code == 404:
        raise ValueError("Resource not found.")

    if response.status_code not in (200, 201):
        raise RuntimeError(f"GitHub API Error {response.status_code}: {response.text}")

    return response.json()


def git_delete(endpoint: str, json: dict = None):
    headers = _auth_headers()
    response = _request_with_retry("DELETE", endpoint, headers=headers, json=json)

    if response.status_code == 404:
        raise ValueError("Resource not found.")

    if response.status_code not in (200, 204):
        raise RuntimeError(f"GitHub API Error {response.status_code}: {response.text}")

    if response.status_code == 204 or not response.content:
        return {"status": "success"}

    return response.json()


def github_patch(endpoint: str, payload: dict):
    headers = _auth_headers()
    response = _request_with_retry("PATCH", endpoint, headers=headers, json=payload)

    if response.status_code == 404:
        raise ValueError("Resource not found.")

    if response.status_code not in (200, 201):
        raise RuntimeError(f"GitHub API Error {response.status_code}: {response.text}")

    return response.json()
