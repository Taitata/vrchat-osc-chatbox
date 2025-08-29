import requests
import sounddevice as sd
import soundfile as sf
import io
import threading
import json  
import random
from constants import EMOTION_TO_SPEAKER, EN_DICT, SINGING_SPEAKERS

class VoiceVoxTTS:
    def __init__(self, host: str = "127.0.0.1", port: int = 50021):
        self.base_url = f"http://{host}:{port}"
        self._lock = threading.Lock()

    def speak_with_emotion(self, text: str, emotion: str):      
        if isinstance(emotion, list):
            speaker = random.choice(emotion)
        else:
            speaker_list = EMOTION_TO_SPEAKER.get(emotion, [4])
            speaker = random.choice(speaker_list)

        text_kana = self._preprocess(text)

        # Generate audio query
        query = requests.post(
            f"{self.base_url}/audio_query",
            params={"text": text_kana, "speaker": speaker, "enable_katakana_english": True}
        )
        query.raise_for_status()

        # Parse JSON properly
        query_data = query.json()

        # Synthesize speech
        synth = requests.post(
            f"{self.base_url}/synthesis",
            params={"speaker": speaker},
            data=json.dumps(query_data),   # ✅ correct
            headers={"Content-Type": "application/json"}
        )
        synth.raise_for_status()

        # Play audio
        wav_io = io.BytesIO(synth.content)
        data, samplerate = sf.read(wav_io, dtype="float32")
        with self._lock:
            sd.play(data, samplerate)
            sd.wait()

    # def speak_with_emotion(self, text: str, emotion: str):
    #     if isinstance(emotion, list):
    #         speaker = random.choice(emotion)
    #     else:
    #         speaker_list = EMOTION_TO_SPEAKER.get(emotion, [4])
    #         speaker = random.choice(speaker_list)
    
    #     text_kana = self._preprocess(text)
    
    #     # ---------------------------
    #     # Singing voice synthesis block
    #     # ---------------------------
    #     singing_speaker_name, style_ids = random.choice(list(SINGING_SPEAKERS.items()))
    #     style_id = 6000 # random.choice(style_ids)
    #     print(f"Synthesizing singing with {singing_speaker_name}, style ID {style_id}")
    
    #     # Prepare notes: first note must be silent
    #     notes = [{"id": "silence", "key": None, "frame_length": 15, "lyric": ""}]
    #     for char in text_kana:
    #         if char.strip():
    #             notes.append({"id": f"note_{char}", "key": 60, "frame_length": 45, "lyric": char})
    
    #     # Determine endpoint based on style type
    #     endpoint = "/sing_frame_audio_query"
    
    #     singing_query = requests.post(
    #         f"{self.base_url}{endpoint}",
    #         params={"speaker": style_id},
    #         headers={"Content-Type": "application/json"},
    #         data=json.dumps({"notes": notes})
    #     )
    #     singing_query.raise_for_status()
    #     singing_query_data = singing_query.json()
    
    #     # Only call f0/volume if style_id is frame_decode
    #     if style_id < 6000:  # frame_decode styles have IDs < 6000 in your setup
    #         f0_resp = requests.post(
    #             f"{self.base_url}/f0",
    #             params={"speaker": style_id},
    #             headers={"Content-Type": "application/json"},
    #             data=json.dumps(singing_query_data)
    #         )
    #         f0_resp.raise_for_status()
    
    #         volume_resp = requests.post(
    #             f"{self.base_url}/volume",
    #             params={"speaker": style_id},
    #             headers={"Content-Type": "application/json"},
    #             data=json.dumps(singing_query_data)
    #         )
    #         volume_resp.raise_for_status()
    
    #     # Synthesize audio
    #     synth_resp = requests.post(
    #         f"{self.base_url}/frame_synthesis",
    #         params={"speaker": style_id},
    #         headers={"Content-Type": "application/json"},
    #         data=json.dumps(singing_query_data)
    #     )
    #     synth_resp.raise_for_status()
    #     wav_io = io.BytesIO(synth_resp.content)
    #     data, samplerate = sf.read(wav_io, dtype="float32")
    #     with self._lock:
    #         sd.play(data, samplerate)
    #         sd.wait()
    
    #     # ---------------------------
    #     # Normal speech TTS block
    #     # ---------------------------
    #     query = requests.post(
    #         f"{self.base_url}/audio_query",
    #         params={"text": text_kana, "speaker": speaker, "enable_katakana_english": True}
    #     )
    #     query.raise_for_status()
    #     query_data = query.json()
    
    #     synth = requests.post(
    #         f"{self.base_url}/synthesis",
    #         params={"speaker": speaker},
    #         data=json.dumps(query_data),
    #         headers={"Content-Type": "application/json"}
    #     )
    #     synth.raise_for_status()
    
    #     wav_io = io.BytesIO(synth.content)
    #     data, samplerate = sf.read(wav_io, dtype="float32")
    #     with self._lock:
    #         sd.play(data, samplerate)
    #         sd.wait()
    

    def _preprocess(self, text: str) -> str:
        """Convert English words/acronyms to Katakana for VOICEVOX."""
        result = []
        for token in text.split():
            upper_token = token.upper()
            if upper_token in EN_DICT:
                result.append(EN_DICT[upper_token])
            elif token.isascii() and token.isupper():
                katakana = " ".join([EN_DICT.get(c, f"{c}") for c in upper_token])
                result.append(katakana)
            else:
                result.append(token)
        return " ".join(result)  # ✅ keep spaces

