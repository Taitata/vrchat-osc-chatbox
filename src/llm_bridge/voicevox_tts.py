import numpy as np
import requests
import sounddevice as sd
import soundfile as sf
import io
import threading
import json  
import random
from constants import EMOTION_TO_SPEAKER, EN_DICT, SINGING_SPEAKERS, ROMAJI_TO_KATAKANA
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
            
        # 🔹 Ensure 2D shape (channels)
        if data.ndim == 1:
            data = data[:, np.newaxis]

        device_index=21

        # Print all devices with channel info
        #devices = sd.query_devices()
        #for i, dev in enumerate(devices):
        #    print(f"Device {i}: {dev['name']}")
        #    print(f"   Max output channels: {dev['max_output_channels']}")
        #    print(f"   Max input channels:  {dev['max_input_channels']}")

        # Make sure at least one channelk
        dev_info = sd.query_devices(device_index)
        #print(sd.query_devices())
        max_channels = dev_info['max_output_channels']
    
        if max_channels == 0:
            raise ValueError(f"Device {device_index} has 0 output channels!")
    
        print(f"Speaker ID: {speaker}")

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

    def speak_with_emotion3(self, text: str, emotion: str):
        if isinstance(emotion, list):
            speaker = random.choice(emotion)
        else:
            speaker_list = EMOTION_TO_SPEAKER.get(emotion, [4])
            speaker = random.choice(speaker_list)

        text_kana = self._preprocess(text)

        query = requests.post(
            f"{self.base_url}/audio_query",
            params={"text": text_kana, "speaker": speaker, "enable_katakana_english": True}
        )
        query.raise_for_status()
        query_data = query.json()

        print("\n[SPEAK custom] before tweaks:",
              {"pitchScale": query_data.get("pitchScale"),
               "intonationScale": query_data.get("intonationScale")})

        # === Apply tweaks ===
        query_data["pitchScale"] = query_data.get("pitchScale", 0.0) + 0.3
        query_data["intonationScale"] = 1.5

        print("[SPEAK custom] after tweaks:",
              {"pitchScale": query_data["pitchScale"],
               "intonationScale": query_data["intonationScale"]})

        synth = requests.post(
            f"{self.base_url}/synthesis",
            params={"speaker": speaker},
            data=json.dumps(query_data),
            headers={"Content-Type": "application/json"}
        )
        synth.raise_for_status()

        wav_io = io.BytesIO(synth.content)
        data, samplerate = sf.read(wav_io, dtype="float32")
        if data.ndim == 1:
            data = data[:, np.newaxis]
        device_index = 22
        dev_info = sd.query_devices(device_index)
        max_channels = dev_info['max_output_channels']
        if data.shape[1] < max_channels:
            data = np.tile(data, (1, max_channels // data.shape[1]))
        with self._lock:
            sd.play(data, samplerate, device=device_index)
            sd.wait()

    def sing3(self, voicevox_json: str, lyrics: str, emotion: str):
        if isinstance(emotion, list):
            emotionId = random.choice(emotion)
        else:
            speaker_list = EMOTION_TO_SPEAKER.get(emotion, [4])
            emotionId = random.choice(speaker_list)

        all_singers = [s for group in SINGING_SPEAKERS.values() for s in group]
        style_id = random.choice(all_singers)

        resp = requests.post(f"{self.base_url}/sing_frame_audio_query",
                             params={"speaker": 6000}, json=voicevox_json, timeout=10)
        resp.raise_for_status()
        base_query = resp.json()

        print("\n[SING custom] before tweaks:",
              {"f0_first10": base_query["f0"][:10],
               "volume_first10": base_query["volume"][:10]})

        # === Apply tweaks ===
        base_query["f0"] = [f * 1.2 if f > 0 else 0 for f in base_query["f0"]]
        base_query["volume"] = [v * 0.8 for v in base_query["volume"]]

        print("[SING custom] after tweaks:",
              {"f0_first10": base_query["f0"][:10],
               "volume_first10": base_query["volume"][:10]})

        res = requests.post(f"{self.base_url}/frame_synthesis",
                            params={"speaker": style_id}, json=base_query, timeout=30)
        res.raise_for_status()

        wav_io = io.BytesIO(res.content)
        data, samplerate = sf.read(wav_io, dtype="float32")
        with self._lock:
            sd.play(data, samplerate)
            sd.wait()

    def speak_with_emotion4(self, text: str, emotion: str):
        """
        More natural talk:
         1) convert English tokens to katakana using your _preprocess (keeps your EN_DICT)
         2) call /accent_phrases?text=...&speaker=... to get accent phrase segmentation
         3) call POST /mora_data?speaker=... with accent_phrases to get pitch/length info
         4) assemble AudioQuery-like object and call /synthesis
        Prints before/after tweaks.
        """
        # --- choose speaker ---
        if isinstance(emotion, list):
            speaker = random.choice(emotion)
        else:
            speaker_list = EMOTION_TO_SPEAKER.get(emotion, [4])
            speaker = random.choice(speaker_list)

        # prepare text
        text_kana = self._preprocess(text)

        try:
            # 1) get accent phrases
            print(f"\n[ACCEPT] Requesting /accent_phrases for speaker={speaker} text='{text_kana}'")
            r = requests.post(
                f"{self.base_url}/accent_phrases",
                params={"text": text_kana, "speaker": speaker, "enable_katakana_english": True}
            )
            r.raise_for_status()
            accent_phrases = r.json()
            print("[ACCEPT] Received accent_phrases (first phrase):", accent_phrases[0] if accent_phrases else None)

            # 2) get mora data
            print(f"[MORA] Requesting /mora_data for speaker={speaker} with {len(accent_phrases)} accent_phrases")
            r2 = requests.post(
                f"{self.base_url}/mora_data",
                params={"speaker": speaker},
                json=accent_phrases,
                timeout=10
            )
            r2.raise_for_status()
            mora_result = r2.json()
            print("[MORA] Received mora_data (first phrase sample):", mora_result[0] if mora_result else None)

            # 3) build AudioQuery
            audio_query = {
                "accent_phrases": mora_result,
                "speedScale": 1.0,
                "pitchScale": 0.0,
                "intonationScale": 1.0,
                "volumeScale": 1.0,
                "prePhonemeLength": 0.05,
                "postPhonemeLength": 0.05,
                "pauseLength": None,
                "pauseLengthScale": 1.0,
                "outputSamplingRate": 24000,
                "outputStereo": True,
                "kana": text_kana
            }

            print("[SPEAK NATURAL] Audio query before tweaks: speedScale={}, pitchScale={}, intonationScale={}".format(
                audio_query["speedScale"], audio_query["pitchScale"], audio_query["intonationScale"]
            ))

            # --- Optional tweaks for liveliness ---
            audio_query["pitchScale"] += 0.25
            audio_query["intonationScale"] *= 1.25

            print("[SPEAK NATURAL] Audio query after tweaks: pitchScale={}, intonationScale={}".format(
                audio_query["pitchScale"], audio_query["intonationScale"]
            ))

            # 4) synthesize
            synth = requests.post(
                f"{self.base_url}/synthesis",
                params={"speaker": speaker},
                data=json.dumps(audio_query),
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            synth.raise_for_status()

            # play back
            wav_io = io.BytesIO(synth.content)
            try:
                data, samplerate = sf.read(wav_io, dtype='float32')
            except RuntimeError:
                samplerate = 44100
                data = np.zeros((samplerate, 1), dtype='float32')

            if data.ndim == 1:
                data = data[:, np.newaxis]

            device_index = 22
            dev_info = sd.query_devices(device_index)
            max_channels = dev_info['max_output_channels']
            if max_channels == 0:
                raise ValueError(f"Device {device_index} has 0 output channels!")

            if data.shape[1] < max_channels:
                repeats = max_channels // data.shape[1]
                remainder = max_channels % data.shape[1]
                data = np.tile(data, (1, repeats))
                if remainder > 0:
                    data = np.hstack([data, data[:, :remainder]])
            elif data.shape[1] > max_channels:
                data = data[:, :max_channels]

            with self._lock:
                sd.play(data, samplerate, device=device_index)
                sd.wait()

        except requests.exceptions.HTTPError as e:
            print("HTTP error during speak_natural:", e)
            try:
                print("Response JSON:", e.response.json())
            except Exception:
                print("Response text:", e.response.text)
            raise
        except Exception as e:
            print("Error in speak_natural:", e)
            raise

    # -----------------------
    # NATURAL SINGING
    # ------------------------
    def sing4(self, voicevox_json: str, lyrics: str, emotion: str):
        """
        Natural English singing using VOICEVOX frame_synthesis:
          1) Convert English lyrics -> Katakana using _preprocess
          2) Pick style_id (singing speaker) and emotionId
          3) Request /sing_frame_audio_query to get valid frame query
          4) Optional tweaks: slight pitch wobble + volume scaling for naturalness
          5) POST full frame_audio_query to /frame_synthesis
        """
        # --- choose emotion -> emotionId ---
        if isinstance(emotion, list):
            emotionId = random.choice(emotion)
        else:
            speaker_list = EMOTION_TO_SPEAKER.get(emotion, [4])
            emotionId = random.choice(speaker_list)

        # --- choose singing style_id ---
        all_singers = [s for group in SINGING_SPEAKERS.values() for s in group]
        if not all_singers:
            raise RuntimeError("No singing speakers available in SINGING_SPEAKERS constant")
        style_id = random.choice(all_singers)

        # --- convert lyrics to Katakana for printing/logging ---
        lyrics_kana = self._preprocess(lyrics)
        print(f"[SING EN] Using style_id={style_id}, emotionId={emotionId}")
        print("[SING EN] Katakana lyrics:", lyrics_kana)

        try:
            # --- 1) Request a valid frame_audio_query from VOICEVOX ---
            print(f"[SING EN] Requesting /sing_frame_audio_query with style_id={style_id}")
            resp = requests.post(
                f"{self.base_url}/sing_frame_audio_query",
                params={"speaker": 6000},
                json=voicevox_json,
                timeout=15
            )
            resp.raise_for_status()
            frame_query = resp.json()

            print("[SING EN] Frame query built:", len(frame_query.get("f0", [])), "frames")
            print("[SING EN] Sample phonemes:", frame_query.get("phoneme", [])[:10])

            # --- 2) Optional tweaks for naturalness ---
            # small longitudinal pitch modulation to simulate vibrato
            import math
            f0 = frame_query.get("f0", [])
            for i in range(len(f0)):
                if f0[i] > 0:
                    wobble = 1.0 + 0.01 * math.sin(2 * math.pi * i / 120)
                    f0[i] *= wobble
            frame_query["f0"] = f0

            # slightly reduce volume to avoid clipping
            if "volume" in frame_query:
                frame_query["volume"] = [v * 0.95 for v in frame_query["volume"]]

            print("[SING EN] f0 and volume tweaked for naturalness")

            # --- 3) POST full frame_audio_query to /frame_synthesis ---
            print(f"[SING EN] Calling /frame_synthesis with style_id={style_id}")
            res = requests.post(
                f"{self.base_url}/frame_synthesis",
                params={"speaker": style_id},
                json=frame_query,
                timeout=60
            )
            res.raise_for_status()

            # --- 4) Play the returned audio ---
            wav_io = io.BytesIO(res.content)
            data, samplerate = sf.read(wav_io, dtype="float32")
            if data.ndim == 1:
                data = data[:, np.newaxis]

            with self._lock:
                sd.play(data, samplerate)
                sd.wait()

        except requests.exceptions.HTTPError as e:
            print("VOICEVOX API returned an error during sing!")
            print("Status code:", e.response.status_code)
            try:
                print("Response JSON:", e.response.json())
            except Exception:
                print("Response text:", e.response.text)
            raise
        except Exception as e:
            print("Error in sing():", e)
            raise

