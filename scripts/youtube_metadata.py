"""
youtube_metadata.py — The Uptick (Drama about Money)
"""
import re
import unicodedata

MAX_TAGS_CHARS = 480
MAX_TITLE_CHARS = 95
MAX_DESCRIPTION_CHARS = 4800


def _sanitize_tag(tag: str) -> str:
    tag = unicodedata.normalize("NFKD", str(tag))
    tag = re.sub(r'[^\x00-\x7F]', '', tag)
    tag = re.sub(r'[<>&"\'\`\#]', '', tag)
    tag = ' '.join(tag.split())
    return tag.strip()[:100]


def _dedupe_preserve_order(items):
    seen = set()
    out = []
    for item in items:
        clean = _sanitize_tag(item)
        key = clean.lower()
        if key and key not in seen:
            seen.add(key)
            out.append(clean)
    return out


def build_final_metadata(video: dict, trending_keywords: list[str]) -> dict:
    title = video.get("title", "Money Drama")[:MAX_TITLE_CHARS]

    hashtags = _dedupe_preserve_order(video.get("hashtags", ["#shorts"]))
    hashtag_line = " ".join(hashtags)

    description_parts = [
        video.get("description", "").strip(),
        "",
        hashtag_line,
    ]
    description = "\n".join(p for p in description_parts if p)[:MAX_DESCRIPTION_CHARS]

    combined_tags = _dedupe_preserve_order(
        video.get("tags", []) + trending_keywords + [
            "money story", "money drama", "financial story", "rich story",
            "millionaire story", "wealth story", "money confession",
            "shocking money story", "money struggles", "financial drama",
            "rags to riches", "poor to rich", "lost everything", "found money",
            "greed story", "betrayal story", "success story", "failure story",
            "unexpected money", "lottery story", "inheritance drama",
            "storytime", "story time", "short story", "dramatic story",
            "emotional story", "life story",
            "shorts", "motivation", "inspiration", "money motivation",
            "wealth mindset", "financial freedom",
        ]
    )

    final_tags = []
    char_budget = MAX_TAGS_CHARS
    for tag in combined_tags:
        if len(tag) + 1 > char_budget:
            break
        final_tags.append(tag)
        char_budget -= len(tag) + 1

    return {
        "title": title,
        "description": description,
        "tags": final_tags,
    }
