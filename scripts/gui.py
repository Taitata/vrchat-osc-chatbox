import sys, threading
from pathlib import Path
root=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(root/'src'))
import tkinter as tk
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText
from osc_chatbox.config import SETTINGS
from osc_chatbox.osc_io import ChatboxClient
from llm_bridge.openrouter_adapter import OpenRouterClient
from llm_bridge.hf_adapter import HuggingFaceClient
from llm_bridge.history import ConversationHistory
from llm_bridge.utils import retry_with_backoff,safety_filter
from llm_bridge.tts import TTSClient

def get_llm(provider="none"):
    provider=(provider or SETTINGS.llm_provider).lower()
    if provider=="openrouter": return OpenRouterClient()
    elif provider=="huggingface": return HuggingFaceClient()
    else: raise ValueError(f"Unknown LLM_PROVIDER: {provider}")

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("VRChat LLM Chatbox GUI"); self.geometry("820x560")
        top=ttk.Frame(self); top.pack(fill=tk.X, padx=8, pady=6)
        ttk.Label(top,text="Prompt:").pack(side=tk.LEFT, padx=(0,6))
        self.prompt=ttk.Entry(top,width=70); self.prompt.pack(side=tk.LEFT,fill=tk.X,expand=True); self.prompt.bind("<Return>", self.on_send_return)
        ttk.Button(top,text="Send",command=self.on_send).pack(side=tk.LEFT, padx=6)
        opts=ttk.Frame(self); opts.pack(fill=tk.X, padx=8, pady=(0,6))
        self.tts_var=tk.BooleanVar(value=SETTINGS.enable_tts); ttk.Checkbutton(opts,text="Enable TTS",variable=self.tts_var).pack(side=tk.LEFT)
        self.provider_var=tk.StringVar(value=SETTINGS.llm_provider); ttk.Label(opts,text="Provider:").pack(side=tk.LEFT, padx=(12,4))
        ttk.Combobox(opts,textvariable=self.provider_var,values=["openrouter","huggingface"],width=14).pack(side=tk.LEFT)
        self.log=ScrolledText(self,width=100,height=26,state=tk.DISABLED); self.log.pack(fill=tk.BOTH,expand=True,padx=8,pady=6)
        self.h=ConversationHistory(); self.llm=get_llm(self.provider_var.get())
        self.osc=ChatboxClient(host=SETTINGS.vrchat_ip,port=SETTINGS.osc_in_port,max_len=SETTINGS.chatbox_max_len,debug=SETTINGS.debug)
        self.tts=TTSClient() if self.tts_var.get() else None
        def on_provider_change(*_):
            try:
                self.llm=get_llm(self.provider_var.get()); self.append("[system] Switched provider to: "+self.provider_var.get())
            except Exception as e:
                self.append("[error] "+str(e))
        self.provider_var.trace_add("write", on_provider_change)
    def append(self,text):
        self.log.configure(state=tk.NORMAL); self.log.insert(tk.END,text+"\n"); self.log.configure(state=tk.DISABLED); self.log.see(tk.END)
    def on_send_return(self,event): self.on_send()
    def on_send(self):
        q=self.prompt.get().strip()
        if not q: return
        self.prompt.delete(0,tk.END); self.append("You: "+q)
        threading.Thread(target=self._llm_call_and_send,args=(q,),daemon=True).start()
    def _llm_call_and_send(self,q):
        def call(): return self.llm.complete(q,history=self.h)
        try: r=retry_with_backoff(call)
        except Exception as e:
            self.append("[error] LLM call failed: "+str(e)); return
        safe=safety_filter(r); self.h.add_turn(q,safe); self.append("Bot: "+safe)
        try:
            self.osc.typing(True); self.osc.say(safe)
        finally:
            self.osc.typing(False)
        if self.tts_var.get():
            if self.tts is None: self.tts=TTSClient()
            self.tts.speak(safe)
if __name__=="__main__": App().mainloop()
