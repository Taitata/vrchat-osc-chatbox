import os
from huggingface_hub import InferenceClient
from .base import LLMClient
from .utils import complete_with_client

class HuggingFaceClient(LLMClient):
    def __init__(self, api_key=None, model=None):
        self.api_key = api_key or os.getenv("HF_API_KEY")
        self.model = model or os.getenv("HF_MODEL")
        if not self.api_key or not self.model:
            raise ValueError("HF_API_KEY or HF_MODEL not set")
        self.client = InferenceClient(token=self.api_key)

    def complete(self, prompt: str, history=None) -> dict:
        return complete_with_client(self.client, self.model, prompt)