from langchain_mcp_adapters.client import MultiServerMCPClient

SERVERS = {
    "ForgeMCP": {
        "transport": "streamable_http",
        "url": "https://gitserver-production.up.railway.app/mcp",
        "headers": {
            "Authorization": "Bearer KUm725H1HOhChd0Wkclg1UVQMtqU4w4D16fgzTmQEq8"
        }
    }
}


async def get_mcp_tools():
    client = MultiServerMCPClient(SERVERS)
    tools = await client.get_tools()
    return tools
