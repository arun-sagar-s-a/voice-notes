""" Use the Groq API client for Whisper transcription + Llama expense parsing."""

import os, json, httpx, yaml
from pathlib import Path

API_KEY             = os.environ["GROQ_API_KEY"]
BASE_URL            = "https://api.groq.com/openai/v1"

TRANSCRIPTION_MODEL = "whisper-large-v3-turbo"

#  LLM_MODEL           = "llama-3.3-70b-versatile"
FALLBACK_LLM_MODEL  = ["llama-3.3-70b-versatile", "meta-llama/llama-4-scout-17b-16e-instruct"] 

PROMPTS_DIR = Path(__file__).parent.parent/"prompts"

def load_prompt(name: str) -> dict:
    config_path = PROMPTS_DIR / f"{name}.yaml"
    with open(config_path) as f:
        config = yaml.safe_load(f)
    
    prompt_path = PROMPTS_DIR / config["prompt_file"]
    with open(prompt_path) as f:
        config["system"] = f.read()
    
    return config

async def transcribe_audio(audio_bytes: bytes, filename: str) -> dict:
    async with httpx.AsyncClient(timeout=120.0) as client:
        resp = await client.post(
            f"{BASE_URL}/audio/transcriptions",
            headers={"Authorization": f"Bearer {API_KEY}"},
            files={"file":(filename, audio_bytes)},
            data={
                "model":TRANSCRIPTION_MODEL,
                "response_format":"verbose_json",
            },
        )
        resp.raise_for_status()
        data = resp.json()
        return{
            "text": data["text"],
            "duration":data.get("duration",0.0)
        }
    
async def parse_expense(transcript: str) -> dict:
    prompt_config = load_prompt("parse_expenses")
    system_prompt = prompt_config["system"]
    temperature = prompt_config["temperature"]
    errors = []

    for model in FALLBACK_LLM_MODEL:
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(
                    f"{BASE_URL}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {API_KEY}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model":model,
                        "messages": [
                            {"role":"system","content": system_prompt},
                            {"role":"user","content":f"Parse this expense:\n\n {transcript}"}
                        ],
                        "temperature": temperature,
                    }
                )
                resp.raise_for_status()
                content = resp.json()["choices"][0]["message"]["content"]
                content = content.strip()
                if content.startswith("```"):
                    content = content.split("\n", 1)[1].rsplit("```", 1)[0]

                return json.loads(content)
            
        except Exception as e:
            errors.append(f"{model}: {type(e).__name__}: {e}")
            continue
    
    raise Exception("All models failed. collective errors \n:".join(errors))