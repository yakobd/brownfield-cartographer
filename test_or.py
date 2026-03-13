import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY")
)

print("Connecting to OpenRouter (Free Model)...")

try:
    completion = client.chat.completions.create(
        model="google/gemma-3-27b-it:free", 
        messages=[{"role": "user", "content": "Say 'System Online'"}]
    )
    print(f"RESULT: {completion.choices[0].message.content}")
except Exception as e:
    print(f"FAILED: {e}")