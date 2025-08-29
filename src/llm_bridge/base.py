from abc import ABC, abstractmethod

class LLMClient(ABC):
    @abstractmethod
    def complete(self, prompt: str, history=None) -> str:
        raise NotImplementedError
