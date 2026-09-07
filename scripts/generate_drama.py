"""
generate_drama.py — The Uptick (Drama about Money) with AI scene images
Per-scene AI image prompts with character consistency across all scenes.
"""
import json
import os
import random
from pathlib import Path

import anthropic

client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

STATE_SUFFIX = os.environ.get("STATE_SUFFIX", "")
STATE_FILE = Path(__file__).resolve().parent.parent / "state" / f"used_premises{STATE_SUFFIX}.json"

STORY_ARCHETYPES = [
    "A person finds or receives a life-changing amount of money unexpectedly",
    "Someone loses everything they built — and what they do next",
    "A single financial decision that changed someone's entire life",
    "Greed destroys a relationship, partnership, or family",
    "A person walks away from enormous wealth — and why",
    "Someone discovers a financial secret that changes everything",
    "An extreme act of generosity and what it costs the giver",
    "A lottery winner's life goes completely wrong",
    "A rags-to-riches story with a twist nobody saw coming",
    "A betrayal over money between people who trusted each other",
    "Someone bets everything on one thing — and the result",
    "A person living secretly rich or secretly broke",
    "An inheritance that tears a family apart",
    "A business that succeeded for the wrong reasons",
    "A debt that changed the course of someone's life",
    "Someone who refused money that would have changed everything",
    "The hidden cost of sudden wealth",
]

HOOK_STYLES = [
    "He had $3 million in the bank. He had never been more miserable.",
    "She found an envelope with $80,000 inside. What she did next divided the internet.",
    "They offered him the job of his dreams. He turned it down. Here's why.",
    "She worked three jobs for fifteen years. Then one phone call changed everything.",
    "He gave away his entire fortune. His family never forgave him.",
    "They were best friends for twenty years. One investment destroyed all of it.",
    "She made $4 million before she turned thirty. She was broke by thirty-two.",
    "He discovered his company had been lying to him for a decade.",
    "They found $200,000 in the walls of a house they just bought.",
]

SYSTEM_PROMPT = """You write scripts for a YouTube Shorts channel called The Uptick,
which tells original short dramatic stories about money — greed, unexpected wealth,
devastating loss, betrayal, redemption, and impossible choices.

Fictional but feels completely real. Style: dramatic voiceover narration, third person,
short punchy sentences, building tension toward a twist or resolution.

CONTENT RULES:
- Entirely original — no real named people, companies, or specific places
- Dramatic but not gratuitous — emotional and financial stakes, not violence
- Clear protagonist, money-related conflict, resolution with a twist

STRUCTURE:
1. HOOK (1-2 sentences): Start in the middle of the drama — most gripping moment first
2. BEATS (5-6): 1-2 sentences each advancing the story
3. CLOSE (1 sentence): The final sting or moral

TARGET: 30-40 seconds spoken aloud.

CHARACTER CONSISTENCY (most important for image quality):
First define the main character visually — be specific:
"A 38-year-old South Asian woman with shoulder-length black hair, wearing a grey blazer
and white blouse, sharp eyes, no jewelry except small gold earrings"
This EXACT character_description must be copy-pasted word-for-word into the start of
EVERY scene's image_prompt. Only the action and setting change.

IMAGE PROMPT FORMAT (for every scene):
"IMPORTANT: Keep each image_prompt under 900 characters total including the
character description. Be specific but brief — "dramatic side lighting,
shock on her face, laptop screen glow" beats a paragraph of description.

Cinematic photorealistic film still, 9:16 vertical portrait format, [lighting type].
[PASTE CHARACTER DESCRIPTION WORD FOR WORD]. [What character is doing, where, emotional
expression, key props in frame]. Shot on Sony A7, shallow depth of field, [color grade]."

Lighting and color grade examples by scene mood:
- Discovery/shock: "harsh fluorescent office lighting, cold blue-white color grade"
- Tension/conflict: "dramatic side lighting, deep shadows, desaturated color grade"
- Loss/grief: "overcast natural light, muted warm tones, shallow focus"
- Resolution/turn: "golden hour window light, warm amber color grade"
- Triumph/relief: "bright natural light, slightly lifted exposure"

TITLE STRATEGY (SEO-critical):
- Include specific dollar amount: "$3 Million", "$80,000", "$500K"
- Proven patterns: "He Made $X and Lost It All", "She Found $X. Then [consequence]."
- Under 70 characters for mobile

Call the submit_drama_video tool exactly once."""

DRAMA_TOOL = {
    "name": "submit_drama_video",
    "description": "Submit the finished money drama with per-scene AI image prompts.",
    "input_schema": {
        "type": "object",
        "properties": {
            "premise": {"type": "string", "description": "One-sentence summary to avoid repeating"},
            "title": {"type": "string", "description": "<=95 chars. Include dollar amount. Dramatic and specific."},
            "description": {"type": "string", "description": "2-3 sentences teasing story without spoiling twist, plus follow nudge with keywords: money stories, financial drama, wealth confession"},
            "tags": {"type": "array", "items": {"type": "string"}, "description": "8-12 lowercase tags: money story, drama, greed, betrayal, rags to riches, millionaire, shocking, storytime, etc."},
            "hashtags": {"type": "array", "items": {"type": "string"}, "description": "5-8 hashtags, always include #shorts and #moneystory"},
            "character_description": {
                "type": "string",
                "description": "Specific visual description of main character: age, hair color/style, skin tone, clothing, distinguishing features. This exact text goes word-for-word into every image_prompt."
            },
            "hook": {"type": "string", "description": "1-2 sentences. Start in the middle of the drama."},
            "hook_image_prompt": {
                "type": "string",
                "description": "Full cinematic prompt: start with format/lighting, paste character_description word for word, then scene-specific action/emotion/setting/props."
            },
            "beats": {
                "type": "array",
                "minItems": 5,
                "maxItems": 6,
                "items": {
                    "type": "object",
                    "properties": {
                        "narration": {"type": "string", "description": "1-2 sentences advancing the story"},
                        "image_prompt": {"type": "string", "description": "Full cinematic prompt with character_description pasted word for word, plus scene-specific details"},
                    },
                    "required": ["narration", "image_prompt"],
                },
            },
            "close": {"type": "string", "description": "One final sentence — the moral or sting"},
            "close_image_prompt": {"type": "string", "description": "Full cinematic prompt for close scene"},
        },
        "required": ["premise", "title", "description", "tags", "hashtags",
                     "character_description", "hook", "hook_image_prompt",
                     "beats", "close", "close_image_prompt"],
    },
}


def _load_used_premises():
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return []


def _save_used_premise(premise):
    used = _load_used_premises()
    used.append(premise)
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(used[-60:], indent=2))


def generate_drama_video() -> dict:
    used_premises = _load_used_premises()
    avoid_text = (
        "Avoid these recently-used premises:\n" + "\n".join(f"- {p}" for p in used_premises[-20:])
        if used_premises else "No prior premises to avoid yet."
    )
    archetype = random.choice(STORY_ARCHETYPES)
    hook_example = random.choice(HOOK_STYLES)

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2500,
        system=SYSTEM_PROMPT,
        tools=[DRAMA_TOOL],
        tool_choice={"type": "tool", "name": "submit_drama_video"},
        messages=[{
            "role": "user",
            "content": f"""Write today's money drama story.

{avoid_text}

Story archetype: "{archetype}"
Hook style inspiration (adapt — don't copy): "{hook_example}"

Short sentences. One twist. 30-40 seconds.
Copy character_description word-for-word into every image_prompt.""",
        }],
    )

    tool_use_block = next(b for b in response.content if b.type == "tool_use")
    video = dict(tool_use_block.input)

    if not any(h.lower() == "#shorts" for h in video.get("hashtags", [])):
        video.setdefault("hashtags", []).append("#shorts")

    _save_used_premise(video["premise"])
    return video


if __name__ == "__main__":
    print(json.dumps(generate_drama_video(), indent=2))
