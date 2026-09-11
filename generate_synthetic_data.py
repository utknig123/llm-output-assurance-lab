"""
Generate 1k synthetic legal critique examples
using OpenRouter FREE models
"""

import os
import json
import time
import requests
from pathlib import Path
from dotenv import load_dotenv

# Load env from backend/.env (project root) or local .env
_HERE = Path(__file__).resolve().parent
load_dotenv(_HERE.parent / "backend" / ".env")
load_dotenv(_HERE / ".env")

# =====================================================
# OpenRouter Config (FREE)
# =====================================================

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
MODEL = os.getenv("OPENROUTER_MODEL", "meta-llama/llama-3.1-8b-instruct")

if not OPENROUTER_API_KEY:
    raise ValueError(
        "OPENROUTER_API_KEY is not set. Add it to backend/.env or modelBfinetuning/.env"
    )

API_URL = "https://openrouter.ai/api/v1/chat/completions"

HEADERS = {
    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
    "Content-Type": "application/json",
    "HTTP-Referer": "http://localhost",
    "X-Title": "Synthetic Legal Critique Generator"
}

# =====================================================
# API Call
# =====================================================
def call_llm(prompt: str) -> str:
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 2048
    }

    response = requests.post(
        API_URL,
        headers=HEADERS,
        json=payload,
        timeout=120
    )

    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    else:
        raise Exception(f"API error {response.status_code}: {response.text}")

# =====================================================
# Data Generation
# =====================================================
def generate_synthetic_examples(num_examples=1000):

    legal_topics = [
        "contract disputes", "property rights", "employment law",
        "criminal defense", "family law", "intellectual property",
        "tax law", "immigration", "corporate law", "labor law",
        "consumer protection", "environmental law",
        "constitutional law", "administrative law",
        "tort law", "commercial law"
    ]

    examples = []

    print(f"Generating {num_examples} synthetic critique examples...")

    for i in range(num_examples):
        if (i + 1) % 25 == 0:
            print(f"Progress: {i + 1}/{num_examples}")

        topic = legal_topics[i % len(legal_topics)]

        prompt = f"""
Generate a synthetic legal question-answer-critique example for training a critique model.

Legal Topic: {topic}

Generate:
1. A realistic legal question (2–3 sentences)
2. An initial legal answer with some legal errors (200–300 words)
3. A critique identifying errors in 8 categories:
   - Factual accuracy
   - Logical reasoning
   - Legal terminology
   - Completeness
   - Compliance
   - Structure
   - Context
   - Practical applicability

STRICT JSON ONLY:
{{
  "question": "...",
  "answer": "...",
  "critique": "One line per category"
}}
"""

        try:
            text = call_llm(prompt)

            start = text.find("{")
            end = text.rfind("}") + 1

            if start != -1 and end > start:
                example = json.loads(text[start:end])
                examples.append(example)
            else:
                print(f"⚠️ JSON parse failed at {i+1}")

            time.sleep(1)  # free tier safe

        except Exception as e:
            print(f"❌ Error at {i+1}: {e}")
            time.sleep(3)

    print(f"\n✅ Generated {len(examples)} examples")
    return examples

# =====================================================
# Save
# =====================================================
def save_examples(examples):
    os.makedirs("data", exist_ok=True)
    path = "data/synthetic_critique_data.json"

    with open(path, "w", encoding="utf-8") as f:
        json.dump(examples, f, indent=2, ensure_ascii=False)

    print(f"💾 Saved to {path}")

# =====================================================
# Main
# =====================================================
if __name__ == "__main__":
    data = generate_synthetic_examples(1000)
    save_examples(data)
    print("\n🎉 Done!")






