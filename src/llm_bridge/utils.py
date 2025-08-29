import os, re, time, random
from constants import JSON_PROMPT_TEMPLATE, EMOTION_TO_SPEAKER
import json

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


def prepare_prompt(prompt: str) -> str:
    return JSON_PROMPT_TEMPLATE.format(
        prompt=prompt,
        emotions=", ".join(EMOTION_TO_SPEAKER.keys())
    )

def parse_llm_json_response(raw: str) -> dict:
    cleaned = re.sub(r"^```[a-zA-Z]*\n|```$", "", raw, flags=re.DOTALL).strip()
    try:
        data = json.loads(cleaned)
        if "reply" not in data or "emotion" not in data:
            raise ValueError("Missing keys in LLM response")
    except Exception:
        data = {"reply": cleaned, "emotion": ""}
    return data

def complete_with_client(client, model: str, prompt: str) -> dict:
    json_prompt = prepare_prompt(prompt)
    resp = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": json_prompt}],
        max_tokens=200
    )
    return parse_llm_json_response(resp.choices[0].message.content.strip())
