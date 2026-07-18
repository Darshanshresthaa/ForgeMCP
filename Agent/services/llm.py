import os
from dotenv import load_dotenv

from langchain_mistralai import ChatMistralAI


load_dotenv()

def get_mistral_llm():
    model = ChatMistralAI(
        model="mistral-small-latest",
        api_key=os.getenv("MISTRAL_API_KEY")
    )

    return model


