"""
generate_images.py
Calls OpenAI's image API to generate one AI image per scene.
Uses gpt-image-1-mini at low quality by default — cheap enough
(under $0.02 per image) for daily automation.
"""
import base64
import os
from pathlib import Path

import requests

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
OPENAI_IMAGE_MODEL = os.environ.get("OPENAI_IMAGE_MODEL", "gpt-image-1-mini")
OPENAI_IMAGE_QUALITY = os.environ.get("OPENAI_IMAGE_QUALITY", "low")


def generate_scene_image(prompt: str, output_path: str) -> str:
    """
    Generate one image from a text prompt and save it as PNG.
    Returns the output path on success, raises on failure.
    """
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
            "size": "1024x1792",  # portrait 9:16 ratio
            "quality": OPENAI_IMAGE_QUALITY,
            "response_format": "b64_json",
        },
        timeout=120,
    )
    resp.raise_for_status()

    image_data = resp.json()["data"][0]["b64_json"]
    image_bytes = base64.b64decode(image_data)

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "wb") as f:
        f.write(image_bytes)

    return output_path


if __name__ == "__main__":
    generate_scene_image(
        "Cinematic photorealistic film still, dramatic side lighting. "
        "A woman in a grey blazer staring at a laptop screen, expression of shock.",
        "/tmp/test_scene.png"
    )
    print("Saved /tmp/test_scene.png")
