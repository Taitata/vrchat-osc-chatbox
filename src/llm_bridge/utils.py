import os, re, time, random
import json
import romkan
from music21 import stream, note, meter, converter
from llm_bridge.state import ChatState
from constants import JSON_PROMPT_TEMPLATE, EMOTION_TO_SPEAKER, MODE_TO_SPEAKER, ROMAJI_TO_KATAKANA, KANA_TO_PHONEME

PREFIX_TO_EMOTION = {k[0].lower(): k for k in EMOTION_TO_SPEAKER.keys()}

def retry_with_backoff(func):
    retries=int(os.getenv('MAX_RETRIES','3')); base=int(os.getenv('BACKOFF_BASE_SEC','2'))
    for i in range(retries):
        try: return func()
        except Exception:
            if i==retries-1: raise
            time.sleep(base*(2**i)+random.random())

def safety_filter(text, max_len=2048):
    if not text or not str(text).strip(): return '[Filtered: empty]'
    banned=['suicide','kill yourself','NSFW']; t=str(text)
    for w in banned:
        if re.search(w,t,re.I): return '[Filtered: unsafe]'
    return t[:max_len]

def parse_input(user_input: str) -> None:
    """
    Update chat_state with emotion + call_llm flag.
    """
    # LLM mode
    if user_input.lower().startswith("t:"):
        rest = user_input[2:].strip()
        if rest and rest[0].lower() in PREFIX_TO_EMOTION:
            ChatState.emotion = PREFIX_TO_EMOTION[rest[0].lower()]
        ChatState.call_llm = True
        return

    # TTS mode
    if user_input and user_input[0].lower() in PREFIX_TO_EMOTION:
        ChatState.emotion = PREFIX_TO_EMOTION[user_input[0].lower()]
    ChatState.call_llm = False
    
def prepare_system_prompt() -> str:
    return JSON_PROMPT_TEMPLATE.format(
        emotions=", ".join(EMOTION_TO_SPEAKER.keys()),
        modes=", ".join(MODE_TO_SPEAKER.keys())
    )

def parse_llm_json_response(raw: str) -> dict:
    cleaned = re.sub(r"^```[a-zA-Z]*\n|```$", "", raw, flags=re.DOTALL).strip()
    try:
        data = json.loads(cleaned)
        if "reply" not in data or "emotion" not in data or "mode" not in data:
            raise ValueError("Missing keys in LLM response")
    except Exception:
        data = {"reply": cleaned, "emotion": "neutral", "mode": "talk"}
    return data

def complete_with_client(client, model: str, prompt: str) -> dict:
    system_prompt = prepare_system_prompt()
    user_prompt = prompt.strip()
    print(user_prompt)
    resp = client.chat.completions.create(
        model=model,
        messages=[{"role": "system", "content": system_prompt},{"role": "user", "content": user_prompt}],
        max_tokens=200
    )
    return parse_llm_json_response(resp.choices[0].message.content.strip())


def text_to_musicxml(text: str, outfile="temp.musicxml"):
    s = stream.Score()
    part = stream.Part()
    part.append(meter.TimeSignature("4/4"))

    # Split words into syllables (naively just characters here)
    for ch in text:
        if ch.strip():
            n = note.Note("C4", quarterLength=1)
            n.lyric = ch
            part.append(n)

    s.insert(0, part)
    s.write("musicxml", fp=outfile)
    return outfile

# -------------------------
# 2️⃣ Convert MusicXML file to VOICEVOX JSON
# -------------------------
def musicxml_to_voicevox_json(musicxml_file):
    """
    Parse a MusicXML file and return VOICEVOX JSON dict with notes.
    """
    score = converter.parse(musicxml_file)
    notes_list = []

    for n in score.recurse().notes:
        if n.isNote:
            midi_key = n.pitch.midi
            frame_length = int(n.quarterLength * 45)  # VOICEVOX frame scaling
            lyric = n.lyric if n.lyric else ""
            notes_list.append({
                "key": midi_key,
                "frame_length": frame_length,
                "lyric": lyric
            })
        elif n.isRest:
            frame_length = int(n.quarterLength * 45)
            notes_list.append({
                "key": None,
                "frame_length": frame_length,
                "lyric": ""
            })

    # Add short silence at start and end
    notes_list.insert(0, {"key": None, "frame_length": 15, "lyric": ""})
    notes_list.append({"key": None, "frame_length": 15, "lyric": ""})

    return {"notes": notes_list}

def roman_to_kana(text: str):
    """
    Convert English or romanized text to katakana characters.
    Returns a string of katakana.
    """
    text = text.lower()
    kana_text = []

    i = 0
    while i < len(text):
        # 3-letter match
        if i+2 < len(text) and text[i:i+3] in ROMAJI_TO_KATAKANA:
            kana_text.append(ROMAJI_TO_KATAKANA[text[i:i+3]])
            i += 3
        # 2-letter match
        elif i+1 < len(text) and text[i:i+2] in ROMAJI_TO_KATAKANA:
            kana_text.append(ROMAJI_TO_KATAKANA[text[i:i+2]])
            i += 2
        # 1-letter match
        elif text[i] in ROMAJI_TO_KATAKANA:
            kana_text.append(ROMAJI_TO_KATAKANA[text[i]])
            i += 1
        # Space/punctuation → keep as is (optional: convert to small silence)
        elif text[i] in " ~!,.?":
            kana_text.append(text[i])
            i += 1
        else:
            # fallback for unknown characters
            kana_text.append("ン")
            i += 1

    return "".join(kana_text)

# -------------------------
# 3️⃣ Ensure all note lyrics are valid single Katakana characters
# -------------------------
def convert_lyrics_to_kana(voicevox_json):
    """
    Convert all lyrics to single katakana characters.
    - Remove invalid characters like ー
    - Empty lyrics must have key=None
    """
    for note in voicevox_json["notes"]:
        lyric = note.get("lyric", "").strip()
        if lyric:
            # Convert to katakana
            kana = romkan.to_katakana(lyric)
            # Remove invalid characters (like long vowel marks)
            kana = re.sub(r"[ー]", "", kana)
            # Take the first kana character; fallback to ア if empty
            note["lyric"] = kana[0] if kana else "ア"
        else:
            note["lyric"] = ""
            note["key"] = None
    return voicevox_json


def build_frame_synthesis_object(kana_lyrics, frame_length, f0_value, volume_value):
    phonemes = []
    for kana in kana_lyrics:
        if kana.strip() == "":
            continue
        phoneme = KANA_TO_PHONEME.get(kana, "a")
        phonemes.append({
            "phoneme": phoneme,
            "frame_length": frame_length,
            "note_id": None
        })

    num_frames = len(phonemes) * frame_length

    return {
        "f0": [f0_value] * num_frames,
        "volume": [volume_value] * num_frames,
        "phonemes": phonemes,
        "volumeScale": 1.0,
        "outputSamplingRate": 24000,
        "outputStereo": True
    }

def validate_frame_audio_query(query: dict):
    """Raise ValueError with readable message when query is invalid for frame_synthesis."""
    if "phonemes" not in query or "f0" not in query or "volume" not in query:
        raise ValueError("Missing one of required keys: phonemes, f0, volume")

    # total frames = sum of frame_length for each phoneme
    total_frames = 0
    for p in query["phonemes"]:
        if not isinstance(p.get("phoneme"), str):
            raise ValueError(f"phoneme entry missing/invalid 'phoneme' string: {p!r}")
        if not isinstance(p.get("frame_length"), int):
            raise ValueError(f"phoneme entry missing/invalid 'frame_length' int: {p!r}")
        total_frames += p["frame_length"]

    if len(query["f0"]) != total_frames:
        raise ValueError(f"f0 length ({len(query['f0'])}) != total_frames ({total_frames})")

    if len(query["volume"]) != total_frames:
        raise ValueError(f"volume length ({len(query['volume'])}) != total_frames ({total_frames})")

    # types
    if not all(isinstance(x, (float, int)) for x in query["f0"]):
        raise ValueError("f0 array must contain numbers (float)")
    if not all(isinstance(x, (float, int)) for x in query["volume"]):
        raise ValueError("volume array must contain numbers (float)")
    

def build_frame_audio_query_from_kana(kana_str: str,
                                      frame_length:int=10,
                                      f0_value:float=368.0,
                                      volume_value:float=0.8,
                                      output_sampling_rate:int=24000,
                                      volume_scale:float=1.0,
                                      output_stereo:bool=True):
    """
    Build a minimal FrameAudioQuery compatible with voicevox_engine.model.FrameAudioQuery
    kana_str: string of katakana characters (each kana => one phoneme here)
    """
    phonemes = []
    for ch in kana_str:
        # skip whitespace
        if not ch.strip():
            continue
        phon = KANA_TO_PHONEME.get(ch, "a")
        if phon is None:
            # fallback strategy: use 'pau' (silence) or 'a'
            # but better to raise so you can see unknown kana
            raise ValueError(f"Unknown kana -> phoneme mapping for: {ch!r}. Add to KANA_TO_PHONEME.")
        phonemes.append({"phoneme": phon, "frame_length": int(frame_length)})

    total_frames = sum(p["frame_length"] for p in phonemes)
    # f0 & volume must be arrays length == total_frames
    f0 = [float(f0_value)] * total_frames
    volume = [float(volume_value)] * total_frames

    query = {
        "f0": f0,
        "volume": volume,
        "phonemes": phonemes,
        "volumeScale": float(volume_scale),
        "outputSamplingRate": int(output_sampling_rate),
        "outputStereo": bool(output_stereo)
    }
    validate_frame_audio_query(query)
    return query