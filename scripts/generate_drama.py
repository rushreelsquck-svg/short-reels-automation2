"""
generate_drama.py — The Uptick (Drama about Money)
Generates original short dramatic stories about money — greed, unexpected wealth,
devastating loss, betrayal, redemption, and impossible choices.
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
    "A financial crime where the real victim surprises you",
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

These are fictional but feel completely real — like something that could actually happen.
Think of the style as: dramatic voiceover narration, third person, short punchy sentences,
building tension beat by beat toward a twist or satisfying resolution.

CONTENT RULES:
- Stories must be entirely original — not based on any real named person or actual event
- No real names, no real companies, no real places beyond generic (a city, a bank, a firm)
- Dramatic but not gratuitous — focus on the emotional and financial stakes, not violence
- Every story needs a clear protagonist, a money-related conflict, and a resolution
- The best stories have a detail that reframes everything — a twist nobody saw coming

STRUCTURE:
1. HOOK (1-2 sentences): Start in the middle of the drama — the most gripping moment first.
2. BEATS (5-6): Each beat 1-2 sentences — background, escalation, crisis, turn, resolution.
3. CLOSE (1 sentence): The final sting or moral that stays with the viewer.

NARRATION STYLE:
- Third person. Short sentences. Dramatic.
- Target 30-40 seconds spoken aloud.

VISUAL QUERIES — specific and literal:
- "stack of hundred dollar bills close up", "luxury penthouse interior", "person holding
  head in hands at desk", "empty office after layoff", "two people arguing in office",
  "lawyer reviewing documents", "person staring at phone waiting"

Call the submit_drama_video tool exactly once."""

DRAMA_TOOL = {
    "name": "submit_drama_video",
    "description": "Submit the finished money drama story.",
    "input_schema": {
        "type": "object",
        "properties": {
            "premise": {"type": "string", "description": "One-sentence summary to avoid repeating"},
            "title": {"type": "string", "description": "<=95 chars. SEO-optimized. Include a specific dollar amount when the story has one (e.g. '$3 Million', '$80,000'). Use proven patterns: 'He Made $X and Lost It All', 'She Found $X in [place]. Then [consequence].', 'They Offered Him $X. He Said No.', 'She Was a Millionaire at 29. Broke by 31.' Lead with the most dramatic specific detail — never a vague tease."},
            "description": {"type": "string", "description": "2-3 sentences teasing the story without spoiling the twist, plus a follow nudge"},
            "tags": {"type": "array", "items": {"type": "string"}, "description": "8-12 lowercase tags"},
            "hashtags": {"type": "array", "items": {"type": "string"}, "description": "5-8 hashtags, always include #shorts"},
            "hook": {"type": "string", "description": "1-2 sentences. Start in the middle of the drama."},
            "hook_visual_query": {"type": "string", "description": "Specific literal stock-footage phrase for hook"},
            "beats": {
                "type": "array",
                "minItems": 5,
                "maxItems": 6,
                "items": {
                    "type": "object",
                    "properties": {
                        "narration": {"type": "string", "description": "1-2 sentences advancing the story"},
                        "visual_query": {"type": "string", "description": "Specific literal stock-footage phrase"},
                    },
                    "required": ["narration", "visual_query"],
                },
            },
            "close": {"type": "string", "description": "One final sentence — the moral, the sting, or the reflection"},
            "close_visual_query": {"type": "string", "description": "Specific literal stock-footage phrase for close"},
        },
        "required": ["premise", "title", "description", "tags", "hashtags",
                     "hook", "hook_visual_query", "beats", "close", "close_visual_query"],
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
        max_tokens=2000,
        system=SYSTEM_PROMPT,
        tools=[DRAMA_TOOL],
        tool_choice={"type": "tool", "name": "submit_drama_video"},
        messages=[{
            "role": "user",
            "content": f"""Write today's money drama story.

{avoid_text}

Story archetype for inspiration: "{archetype}"

Example hook style (adapt this energy — don't copy it): "{hook_example}"

Start in the middle of the drama. Short sentences. One twist that reframes everything.
Target: 30-40 seconds spoken aloud.""",
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
