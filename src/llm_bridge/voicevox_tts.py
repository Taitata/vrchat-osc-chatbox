import numpy as np
import requests
import sounddevice as sd
import soundfile as sf
import io
import threading
import json  
import random
from constants import EMOTION_TO_SPEAKER, EN_DICT, SINGING_SPEAKERS
from llm_bridge.utils import build_frame_synthesis_object, build_frame_audio_query_from_kana

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
            data=json.dumps(query_data),
            headers={"Content-Type": "application/json"}
        )
        synth.raise_for_status()
        
        
        # Load wav
        wav_io = io.BytesIO(synth.content)
        try:
            data, samplerate = sf.read(wav_io, dtype='float32')
        except RuntimeError:
            # If file is empty/invalid, generate 1s of silence
            samplerate = 44100
            data = np.zeros((samplerate, 1), dtype='float32')
    
        # Make sure at least one channel
        if data.ndim == 1:
            data = data[:, np.newaxis]  # (N, 1)
        elif data.ndim == 0 or data.shape[1] == 0:
            data = np.zeros((data.shape[0], 1), dtype='float32')

        device_index = 22
        # Match device max output channels
        dev_info = sd.query_devices(device_index)
        max_channels = dev_info['max_output_channels']
    
        if max_channels == 0:
            raise ValueError(f"Device {device_index} has 0 output channels!")
    
        # Expand/reduce channels to match device
        if data.shape[1] < max_channels:
            repeats = max_channels // data.shape[1]
            remainder = max_channels % data.shape[1]
            data = np.tile(data, (1, repeats))
            if remainder > 0:
                data = np.hstack([data, data[:, :remainder]])
        elif data.shape[1] > max_channels:
            data = data[:, :max_channels]
    
        # Play safely
        with self._lock:
            sd.play(data, samplerate, device=device_index)
            sd.wait()
    
        # # Play audio
        # wav_io = io.BytesIO(synth.content)
        # data, samplerate = sf.read(wav_io, dtype="float32")
        # with self._lock:
        #     sd.play(data, samplerate)
        #     sd.wait()

    # ------------------------
    # NEW: SINGING
    # ------------------------
    def sing(self, voicevox_json: str, lyrics: str, emotion: str):
        """
        voicevox_json: the Score-like object produced by musicxml_to_voicevox_json()
        lyrics: the kana lyrics string (you said you run convert_lyrics_to_kana before calling sing)
        emotion: the emotion string -> used to select singer style (speaker id)
        """
        # 1) pick emotion/style id and singer (speaker) consistently
        if isinstance(emotion, list):
            emotionId = random.choice(emotion)
        else:
            speaker_list = EMOTION_TO_SPEAKER.get(emotion, [4])
            emotionId = random.choice(speaker_list)

        # pick a singing speaker (style_id) — but we must use the same id for query generation and frame_synthesis
        all_singers = [s for group in SINGING_SPEAKERS.values() for s in group]
        style_id = random.choice(all_singers)

        # 2) Get initial frame audio query from engine (recommended) using the SAME style_id
        #    This gives you a valid query structure. If you want to override phonemes/f0,
        #    use the returned object as a base and then revalidate.

        try:
            resp = requests.post(f"{self.base_url}/sing_frame_audio_query", params={"speaker": 6000}, json=voicevox_json, timeout=10)
            resp.raise_for_status()
            base_query = resp.json()
        except Exception as e:
            print("Error getting sing_frame_audio_query:", e)
            # print body if present
            try:
                print("Response text:", resp.text)
            except Exception:
                pass
            raise

        # print("initial query (from engine): keys:", list(base_query.keys()))
        
        # # === Safe place to add extra logic ===
        # # Example: adjust f0 or volume without touching phonemes
        # for i in range(len(base_query["f0"])):
        #     base_query["f0"][i] = 368.0          # pitch
        #     base_query["volume"][i] = 0.8   

        # # base_query usually contains phonemes, f0, volume already valid for that style_id

        # # 3) If you must override phonemes/f0/volume, **build a valid FrameAudioQuery** now.
        # #    Example: create a query from the kana 'lyrics' you pass in:
        # try:
        #     custom_query = build_frame_audio_query_from_kana(kana_str=lyrics,
        #                                                      frame_length=10,
        #                                                      f0_value=368.0,
        #                                                      volume_value=0.8,
        #                                                      output_sampling_rate=base_query.get("outputSamplingRate", 24000),
        #                                                      volume_scale=base_query.get("volumeScale", 1.0),
        #                                                      output_stereo=base_query.get("outputStereo", True))
        # except Exception as e:
        #     print("Failed to build custom FrameAudioQuery:", e)
        #     # fallback: use original base_query
        #     custom_query = base_query

        # 4) Use the SAME style_id when calling frame_synthesis
        try:
            # res = requests.post(f"{self.base_url}/frame_synthesis", params={"speaker": style_id}, json=custom_query, timeout=30)
            res = requests.post(f"{self.base_url}/frame_synthesis", params={"speaker": style_id}, json=base_query, timeout=30)
            res.raise_for_status()
        except requests.exceptions.HTTPError as e:
            print("VOICEVOX API returned an error!")
            print("Status code:", e.response.status_code)
            try:
                print("Response JSON:", e.response.json())
            except Exception:
                print("Response text:", e.response.text)
            raise

        
        # Play song
        wav_io = io.BytesIO(res.content)
        data, samplerate = sf.read(wav_io, dtype="float32")
        with self._lock:
            sd.play(data, samplerate)
            sd.wait()

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
        return " ".join(result)
