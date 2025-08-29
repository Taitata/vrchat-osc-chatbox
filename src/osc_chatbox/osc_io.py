import time
from pythonosc.udp_client import SimpleUDPClient
from typing import Iterable

def _chunk(text: str, n: int):
    for i in range(0, len(text), n):
        yield text[i:i+n]

class ChatboxClient:
    def __init__(self, host: str = "127.0.0.1", port: int = 9000,
                 max_len: int = 1400, max_chars_per_msg: int = 2048,
                 delay: float = 5.0, debug: bool = False):
        self.client = SimpleUDPClient(host, port)
        self.max_len = max_len
        self.max_chars_per_msg = max_chars_per_msg
        self.delay = delay
        self.debug = debug

    def typing(self, is_typing: bool) -> None:
        if self.debug:
            print(f"[osc] /chatbox/typing -> {is_typing}")
        self.client.send_message("/chatbox/typing", is_typing)

    def say(self, text: str, press_enter: bool = True) -> None:
        blocks = list(_chunk(text, self.max_chars_per_msg))
        for b_idx, block in enumerate(blocks):
            is_last_block = (b_idx == len(blocks) - 1)
            if self.debug:
                print(f"[osc] Sending block {b_idx+1}/{len(blocks)} ({len(block)} chars)")
            chunks = list(_chunk(block, self.max_len))
            for c_idx, chunk in enumerate(chunks):
                is_last_chunk = (c_idx == len(chunks) - 1)
                enter_flag = bool(press_enter and is_last_block and is_last_chunk)
                if self.debug:
                    print(f"[osc] /chatbox/input -> chunk {c_idx+1}/{len(chunks)} (enter={enter_flag})")
                self.client.send_message("/chatbox/input", [chunk, enter_flag])
            if not is_last_block:
                time.sleep(self.delay)
