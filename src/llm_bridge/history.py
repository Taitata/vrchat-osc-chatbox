import os
from collections import deque
class ConversationHistory:
    def __init__(self, max_turns=None):
        self.max_turns = max_turns or int(os.getenv('HISTORY_MAX_TURNS','5'))
        self.turns = deque(maxlen=self.max_turns)
    def add_turn(self, u, b): self.turns.append((u, b))
    def as_messages(self):
        msgs = []
        for u,b in self.turns:
            msgs.append({'role':'user','content':u}); msgs.append({'role':'assistant','content':b})
        return msgs
