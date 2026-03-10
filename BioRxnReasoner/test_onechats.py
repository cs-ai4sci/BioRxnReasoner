# test_onechats.py
from openai import OpenAI
import os

client = OpenAI(api_key=os.getenv("ONECHATS_API_KEY"),
                base_url=os.getenv("ONECHATS_BASE_URL"))

resp = client.chat.completions.create(
    model=os.getenv("ONECHATS_MODEL", "gpt-4o-mini-2024-07-18"),
    messages=[{"role":"user","content":"hi"}],
    max_tokens=8,
    temperature=0,
)
print(resp.model, "->", resp.choices[0].message.content)
