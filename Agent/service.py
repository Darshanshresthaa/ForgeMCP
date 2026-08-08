import os
from dotenv import load_dotenv
from langchain_mistralai import ChatMistralAI

load_dotenv()


def get_llm():
    model = ChatMistralAI(
        model="mistral-small-latest",
        api_key=os.getenv("MISTRAL_API_KEY"),
        streaming=True,
    )

    return model


def get_mcp_server():
    SERVERS = {
        "ForgeMCP": {
            "transport": "streamable_http",
            "url": "https://git-server-xsj9.onrender.com/mcp",
            "headers": {
                "Authorization": f"Bearer {os.getenv('MCP_AUTH_TOKEN')}"
            },
        }
    }

    return SERVERS


def get_db_uri() -> str:

    """Postgres connection string used for the LangGraph checkpointer (STM)."""

    return os.getenv("DB_URI")
