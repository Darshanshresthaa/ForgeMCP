import os

from MCP.server import mcp
from MCP.Tools import *
from MCP.config import MCP_AUTH_TOKEN

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("MCP_HOST", "127.0.0.1")

    exposed_to_network = host not in ("127.0.0.1", "localhost")

    if exposed_to_network and not MCP_AUTH_TOKEN:
        raise RuntimeError(
            f"Refusing to bind to {host} without MCP_AUTH_TOKEN set in .env. "
            "A network-exposed ForgeMCP server with no auth lets anyone on the "
            "network call delete_repository, delete_file, etc. Either set "
            "MCP_AUTH_TOKEN, or leave MCP_HOST unset to stay on 127.0.0.1."
        )

    mcp.run(transport="http", host=host, port=port)
