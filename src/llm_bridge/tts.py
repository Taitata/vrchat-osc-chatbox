import pyttsx3, threading
class TTSClient:
    def __init__(self, rate: int = 175, volume: float = 0.9):
        self.engine = pyttsx3.init(); self.engine.setProperty("rate", rate); self.engine.setProperty("volume", volume)
        self._lock = threading.Lock()
    def _speak_blocking(self, text: str):
        with self._lock:
            self.engine.say(text); self.engine.runAndWait()
    def speak(self, text: str):
        if not str(text).strip(): return
        threading.Thread(target=self._speak_blocking, args=(text,), daemon=True).start()
