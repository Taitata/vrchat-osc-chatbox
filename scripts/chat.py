import os
import sys
import threading
import json
import re
from pathlib import Path

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / 'src'))

from llm_bridge.state import ChatState
from osc_chatbox.config import SETTINGS
from osc_chatbox.osc_io import ChatboxClient
from llm_bridge.openrouter_adapter import OpenRouterClient
from llm_bridge.hf_adapter import HuggingFaceClient
from llm_bridge.history import ConversationHistory
from llm_bridge.utils import parse_input, retry_with_backoff, text_to_musicxml, musicxml_to_voicevox_json, convert_lyrics_to_kana
from llm_bridge.voicevox_tts import VoiceVoxTTS
from constants import EMOTION_TO_SPEAKER, PREFIX_TO_EMOTION

# ---------------------------------------------
# Initialize LLM provider
# ---------------------------------------------
def get_llm(provider="none"):
    provider = provider or SETTINGS.llm_provider
    print("DEBUG: Using LLM provider =", provider)
    if provider.lower() == "openrouter":
        return OpenRouterClient()
    elif provider.lower() == "huggingface":
        return HuggingFaceClient()
    else:
        raise ValueError(f"Unknown LLM_PROVIDER: {provider}")


# ---------------------------------------------
# Main interactive chat loop
# ---------------------------------------------
def main():
    history = ConversationHistory()
    llm = get_llm(provider=SETTINGS.llm_provider)
    osc = ChatboxClient(
        host=SETTINGS.vrchat_ip,
        port=SETTINGS.osc_in_port,
        max_len=SETTINGS.chatbox_max_len,
        debug=SETTINGS.debug
    )

    # Initialize TTS (Shikoku Metan)
    tts = VoiceVoxTTS() if SETTINGS.enable_tts else None

    print("Interactive chat, Ctrl+C to exit.")
    while True:
        try:
            user_input = input("You: ").strip()
            if not user_input:
               continue
            
            parse_input(user_input)
            if ChatState.call_llm:
                def call():
                    cleaned_input = re.sub(r'^(t:|[{}])'.format("".join(PREFIX_TO_EMOTION.keys())), "", user_input.strip(), flags=re.IGNORECASE).strip()
                    return llm.complete(cleaned_input, history=history)
                
                
                raw_response = retry_with_backoff(call)

                # --------------------------
                # Normalize the response
                # --------------------------
                response_data = {"reply": "", "emotion": "neutral"}
                if isinstance(raw_response, dict):
                    response_data.update(raw_response)
                elif isinstance(raw_response, str):
                    # Strip ```json ... ``` code fences
                    cleaned = re.sub(r"^```[a-zA-Z]*\n|```$", "", raw_response.strip(), flags=re.DOTALL)
                    try:
                        parsed = json.loads(cleaned)
                        if isinstance(parsed, dict):
                            response_data.update(parsed)
                        else:
                            response_data["reply"] = str(parsed)
                    except json.JSONDecodeError:
                        response_data["reply"] = cleaned
                else:
                    response_data["reply"] = str(raw_response)
            
            else:
                response_data = {"reply": user_input, "emotion": "neutral", "mode": "talk"}

            # Extract message and emotion, map to TTS speaker number
            message = response_data.get("reply", "").strip() or user_input
            raw_emotion = response_data.get("emotion", "neutral").lower()
            emotion_speaker = EMOTION_TO_SPEAKER.get(raw_emotion, EMOTION_TO_SPEAKER["neutral"])
            history.add_turn(user_input, message)

            # Print and send to VRChat
            osc.typing(True)
            osc.say(message)
            osc.typing(False)

            mode = response_data.get("mode", "talk") 
            print(f"Bot [{raw_emotion}] [{mode}]: {message}")

            # TTS with detected emotion
            if tts and message:
                if mode == "sing":
                    # Convert bot reply to temporary ABC + MusicXML
                    musicxml_path = "temp.musicxml"
                    lyrics = response_data.get("lyrics", "") 
                    musicxml_file = text_to_musicxml(lyrics, musicxml_path)
                    voicevox_json = musicxml_to_voicevox_json(musicxml_file)
                    voicevox_json = convert_lyrics_to_kana(voicevox_json)
                    threading.Thread(
                        target=tts.sing,
                        args=(voicevox_json, lyrics, emotion_speaker),  # use emotion_speaker like talk
                        daemon=True
                    ).start()
                elif mode == "talk":
                    threading.Thread(
                        target=tts.speak_with_emotion,
                        args=(message, emotion_speaker),  # pass speaker number
                        daemon=True
                    ).start()

        except KeyboardInterrupt:
            print("\nExiting")
            sys.exit(0)


if __name__ == "__main__":
    main()
