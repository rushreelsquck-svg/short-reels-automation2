"""
generate_images.py
Generates one AI image per scene using OpenAI's gpt-image-1 at high quality.
"""
import base64
import os
import time
from pathlib import Path

import requests

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
OPENAI_IMAGE_MODEL = os.environ.get("OPENAI_IMAGE_MODEL", "gpt-image-1")
OPENAI_IMAGE_QUALITY = os.environ.get("OPENAI_IMAGE_QUALITY", "high")

MAX_RETRIES = 3
BASE_DELAY = 10
MAX_PROMPT_CHARS = 900  # gpt-image-1 limit is 1000 — leave headroom


def generate_scene_image(prompt: str, output_path: str) -> str:
    # Truncate prompt if too long
    if len(prompt) > MAX_PROMPT_CHARS:
        prompt = prompt[:MAX_PROMPT_CHARS].rsplit(" ", 1)[0]
        print(f"Prompt truncated to {len(prompt)} chars")

    last_error = None
    for attempt in range(MAX_RETRIES):
        try:
            resp = requests.post(
                "https://api.openai.com/v1/images/generations",
                headers={
                    "Authorization": f"Bearer {OPENAI_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": OPENAI_IMAGE_MODEL,
                    "prompt": prompt,
                    "n": 1,
                    "size": "1024x1536",
                    "quality": OPENAI_IMAGE_QUALITY,
                    "response_format": "b64_json",
                },
                timeout=180,
            )

            if resp.status_code == 429:
                delay = BASE_DELAY * (2 ** attempt)
                print(f"Image API rate limited, retrying in {delay}s...")
                time.sleep(delay)
                last_error = resp.status_code
                continue

            resp.raise_for_status()

            image_data = resp.json()["data"][0]["b64_json"]
            image_bytes = base64.b64decode(image_data)

            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "wb") as f:
                f.write(image_bytes)

            print(f"Image generated: {Path(output_path).name}")
            return output_path

        except Exception as e:
            last_error = e
            if attempt < MAX_RETRIES - 1:
                delay = BASE_DELAY * (2 ** attempt)
                print(f"Image generation failed ({e}), retrying in {delay}s...")
                time.sleep(delay)
            else:
                raise last_error


if __name__ == "__main__":
    generate_scene_image(
        "Cinematic photorealistic film still, dramatic side lighting. "
        "A 40-year-old woman in a grey blazer, expression of shock, "
        "staring at a laptop screen. Cold blue office lighting, Sony A7.",
        "/tmp/test_drama_scene.png"
    )
    print("Saved /tmp/test_drama_scene.png")
