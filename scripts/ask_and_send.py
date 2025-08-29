import argparse
from osc_chatbox.config import SETTINGS
from osc_chatbox.osc_io import ChatboxClient
from llm_bridge.openrouter_adapter import OpenRouterClient
from llm_bridge.history import ConversationHistory
from llm_bridge.utils import retry_with_backoff,safety_filter
def main(argv=None):
    p=argparse.ArgumentParser(description="Part 2: Ask LLM once and send to VRChat"); p.add_argument('--ask'); a=p.parse_args(argv)
    if not a.ask: p.error('--ask required')
    h=ConversationHistory(); llm=OpenRouterClient()
    def call(): return llm.complete(a.ask,history=h)
    r=retry_with_backoff(call); safe=safety_filter(r); h.add_turn(a.ask,safe)
    osc=ChatboxClient(host=SETTINGS.vrchat_ip,port=SETTINGS.osc_in_port,max_len=SETTINGS.chatbox_max_len,debug=SETTINGS.debug)
    try: osc.typing(True); osc.say(safe)
    finally: osc.typing(False)
if __name__=='__main__': main()
