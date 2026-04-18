""" Use the Groq API client for Whisper transcription + Llama expense parsing."""

import os, json, httpx

API_KEY             = os.environ["GROQ_API_KEY"]
BASE_URL            = "https://api.groq.com/openai/v1"

TRANSCRIPTION_MODEL = "whisper-large-v3-turbo"

#  LLM_MODEL           = "llama-3.3-70b-versatile"
FALLBACK_LLM_MODEL  = ["llama-3.3-70b-versatile", "meta-llama/llama-4-scout-17b-16e-instruct"] 

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
    prompt = """You are an expert expense parser. Your job is to extract all expenses from the user's message and output **only** a valid JSON object. Never add explanations, markdown, or any text outside the JSON.

Output format must be exactly:
{
  "expenses": [
    {
      "amount": 10.0,
      "store": "Green Fresh",
      "category": "groceries",
      "notes": "A biweekly snack run"
    }
  ]
}

Rules:
1. Always return an array. If multiple expenses are mentioned, create multiple objects.
2. "amount" MUST be a number (float), never a string. Example: 23.50, not "23.50".
3. "category" must be exactly one of: groceries, food, transport, entertainment, shopping, bills, health, education, other.
4. "store" = business name if clearly mentioned (Costco, Walmart, Green Fresh, Uber, etc.), otherwise null.
5. "notes" = short context if useful, otherwise null. Keep it very brief.
6. If amount is unclear, make your best guess and put "uncertain" in notes.
7. If one store has items from multiple categories and amounts aren't split, assign the full amount to the most appropriate category and put the rest as 0 or split logically if obvious.
8. If no expenses are mentioned at all, return {"expenses": []}

Only output the JSON. No other text."""
    last_error=None

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
                            {"role":"system","content": prompt},
                            {"role":"user","content":f"Parse this expense:\n\n {transcript}"}
                        ],
                        "temperature": 0.1,
                    }
                )
                resp.raise_for_status()
                content = resp.json()["choices"][0]["message"]["content"]
                content = content.strip()
                if content.startswith("```"):
                    content = content.split("\n", 1)[1].rsplit("```", 1)[0]

                return json.loads(content)
            
        except Exception as e:
            last_error = e
            continue
    
    raise Exception(f"All models failed. Last error: {last_error}")