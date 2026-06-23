"""
generate_script.py
Turns a raw headline/summary into:
  - an ORIGINAL ~45-55 second narration script (own words, not copied from the source)
  - a title, description, tags, and hashtags for the upload

Keeping this step "in our own words" is what makes the video non-infringing —
we're reporting on a fact, not republishing anyone's article or footage.

Uses forced tool-use (tool_choice) with a strict JSON schema instead of asking
Claude to free-write JSON as text. That guarantees every required field is
always present and correctly typed — the earlier text-based approach
occasionally omitted a field (e.g. "description") since nothing enforced the
shape of plain text output.
"""
import os

import anthropic

client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

SYSTEM_PROMPT = """You write scripts for a daily YouTube Shorts channel called Coin Loop,
covering trending money, personal finance, investing, and side-hustle news.

Rules:
- Always rewrite the story in completely original wording. Never copy phrases from the source summary.
- Be factual and neutral. Do not invent details that aren't in the source material.
- Report on what happened and why it matters — never tell viewers what to buy, sell, or do with
  their own money. No "you should invest in X," no implied guaranteed returns. This is news
  coverage of money topics, not financial advice, and it should never read like advice.
- Hook viewers in the first 5-7 words, then deliver the story, then a one-line "why it matters" close.
- The script is spoken aloud, so write for the ear: short sentences, no headers, no bullet points.
- Target 110-130 words (about 45-55 seconds at a natural reading pace).
- The title must be accurate to the content — compelling is good, misleading is not.
- Also pick 3-4 short, concrete, visually-literal phrases that a stock-footage search engine
  could find real b-roll for (e.g. "stock market screen", "stack of cash", "person budgeting at laptop",
  "small business storefront") — these become the background footage, cut together in order, so they
  should roughly follow the story's beats. Never use abstract, non-visual, or text-only phrases.
- Call the submit_video_package tool exactly once with the finished package."""

PACKAGE_TOOL = {
    "name": "submit_video_package",
    "description": "Submit the finished title, script, description, tags, hashtags, and background visual cues for this video.",
    "input_schema": {
        "type": "object",
        "properties": {
            "title": {
                "type": "string",
                "description": "<=95 characters, includes a hook, no clickbait that misrepresents the story",
            },
            "script": {
                "type": "string",
                "description": "The spoken narration only, 110-130 words, no headers or bullet points",
            },
            "description": {
                "type": "string",
                "description": "2-4 sentences summarizing the story, plus one line inviting people to follow for daily recaps",
            },
            "tags": {
                "type": "array",
                "items": {"type": "string"},
                "description": "8-12 lowercase keyword tags relevant to this specific story",
            },
            "hashtags": {
                "type": "array",
                "items": {"type": "string"},
                "description": "5-8 hashtags, each starting with #, relevant to this story; always include #shorts",
            },
            "visual_queries": {
                "type": "array",
                "items": {"type": "string"},
                "description": "3-4 short (2-4 word) concrete, literal stock-footage search phrases for this story's background visuals, in story order",
            },
        },
        "required": ["title", "script", "description", "tags", "hashtags", "visual_queries"],
    },
}


def generate_script_package(topic: dict, trending_keywords: list[str] | None = None) -> dict:
    trending_keywords = trending_keywords or []

    user_prompt = f"""Source headline: {topic['title']}
Source summary: {topic.get('summary', '(no summary available, work from the headline only)')}

Currently-trending YouTube keywords you may draw from IF genuinely relevant (do not force-fit ones that don't fit this story): {", ".join(trending_keywords) if trending_keywords else "(none provided)"}"""

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1000,
        system=SYSTEM_PROMPT,
        tools=[PACKAGE_TOOL],
        tool_choice={"type": "tool", "name": "submit_video_package"},
        messages=[{"role": "user", "content": user_prompt}],
    )

    tool_use_block = next(b for b in response.content if b.type == "tool_use")
    package = dict(tool_use_block.input)

    # Always guarantee #shorts is present regardless of what the model produced
    if not any(h.lower() == "#shorts" for h in package.get("hashtags", [])):
        package.setdefault("hashtags", []).append("#shorts")

    return package


if __name__ == "__main__":
    import json

    demo_topic = {"title": "Example headline for a dry run", "summary": "Example summary text."}
    print(json.dumps(generate_script_package(demo_topic), indent=2))
