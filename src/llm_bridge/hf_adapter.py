import os
from huggingface_hub import InferenceClient
from huggingface_hub.utils import HfHubHTTPError
from .base import LLMClient
from .utils import complete_with_client
import requests

class HuggingFaceClient(LLMClient):
    def __init__(self, api_key=None, model=None):
        self.api_key = api_key or os.getenv("HF_API_KEY")
        self.model = model or os.getenv("HF_MODEL")
        if not self.api_key or not self.model:
            raise ValueError("HF_API_KEY or HF_MODEL not set")
        self.client = InferenceClient(token=self.api_key)

    def complete(self, prompt: str, history=None) -> dict:
        try:
            return complete_with_client(self.client, self.model, prompt)
        except (HfHubHTTPError, requests.HTTPError) as e:
            print(f"Using user input as fallback.")
            return {"reply": prompt, "emotion": "neutral", "mode": "talk"}