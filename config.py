import os
from dotenv import load_dotenv
from openai import AsyncOpenAI
from agents import OpenAIChatCompletionsModel

load_dotenv()

# For Gemini:
# BASE_URL: "https://generativelanguage.googleapis.com/v1beta/openai/"
# API_KEY: Your Google AI Studio API key
# MODEL_NAME: "gemini-2.5-flash" (or "gemini-1.5-pro" / "gemini-2.5-pro")

BASE_URL = os.getenv("LLM_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai/")
API_KEY = os.getenv("LLM_API_KEY")
MODEL_NAME = os.getenv("LLM_MODEL_NAME", "gemini-3.5-flash")

if not API_KEY:
    raise ValueError("LLM_API_KEY is not set in the environment variables.")

# Create the standard client pointing to our chosen provider
client = AsyncOpenAI(
    api_key=API_KEY,
    base_url=BASE_URL
)

# Generate a model instance compatible with the OpenAI Agents SDK
def get_titan_model():
    return OpenAIChatCompletionsModel(
        model=MODEL_NAME,
        openai_client=client
    )