from fastmcp import FastMCP
import requests
import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("GITHUB_TOKEN")

HEADERS = {}

if TOKEN:
    HEADERS["Authorization"] = f"Bearer {TOKEN}"


GITHUB_API = "https://api.github.com"


