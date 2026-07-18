from fastmcp import FastMCP
from fastmcp.server.auth.providers.jwt import StaticTokenVerifier

from MCP.config import MCP_AUTH_TOKEN



_auth = None

if MCP_AUTH_TOKEN:
    _auth = StaticTokenVerifier(
        tokens={
            MCP_AUTH_TOKEN: {
                "client_id": "forgemcp-local",
                "scopes": ["tools:use"],
            }
        },
        required_scopes=["tools:use"],
    )

mcp = FastMCP("ForgeMCP", auth=_auth)
