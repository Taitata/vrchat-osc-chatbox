class ChatState:
    def __init__(self):
        self.emotion = "neutral"   # current forced emotion
        self.call_llm = False      # True = LLM, False = TTS

# singleton instance
chat_state = ChatState()