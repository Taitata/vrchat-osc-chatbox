import os
from openai import OpenAI, OpenAIError
from .base import LLMClient
from .utils import complete_with_client

class OpenRouterClient(LLMClient):
    def __init__(self, api_key=None, model=None):
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY") or os.getenv("HF_API_KEY")
        self.model = model or os.getenv("HF_MODEL", "shisa-ai/shisa-v2-llama3.3-70b:free")
        if not self.api_key:
            raise ValueError("OpenRouter API key not provided.")
        self.client = OpenAI(api_key=self.api_key, base_url="https://openrouter.ai/api/v1")

    def complete(self, prompt: str, history=None) -> dict:
        try:
            return complete_with_client(self.client, self.model, prompt)
        except OpenAIError as e:
            print(f"Using user input as fallback.")
            return {"reply": prompt, "emotion": "neutral", "mode": "talk"}