
from pythonosc.udp_client import SimpleUDPClient
from typing import Iterable

def _chunk(text: str, n: int) -> Iterable[str]:
    for i in range(0, len(text), n):
        yield text[i:i+n]

class ChatboxClient:
    def __init__(self, host: str = "127.0.0.1", port: int = 9000, max_len: int = 140, debug: bool = False):
        self.client = SimpleUDPClient(host, port)
        self.max_len = max_len
        self.debug = debug

    def typing(self, is_typing: bool) -> None:
        if self.debug:
            print(f"[osc] /chatbox/typing -> {is_typing}")
        self.client.send_message("/chatbox/typing", is_typing)

    def say(self, text: str, press_enter: bool = True) -> None:
        for chunk in _chunk(text, self.max_len):
            if self.debug:
                print(f"[osc] /chatbox/input -> {chunk!r}, enter={press_enter}")
            self.client.send_message("/chatbox/input", [chunk, press_enter])
