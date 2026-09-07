"""
main.py — The Uptick (Drama about Money)
Fully generative — no news fetching needed.
"""
import json
import os
import sys
import traceback
from pathlib import Path

from generate_drama import generate_drama_video
from generate_audio import generate_voiceover
from build_video import build_video
from fetch_youtube_trending_tags import get_trending_keywords
from youtube_metadata import build_final_metadata
from upload_video import upload_short
from upload_facebook import upload_reel

WORKDIR = Path("/tmp/drama_run")


def run():
    print("[1/5] Writing today's money drama (Claude)...")
    video = generate_drama_video()
    print(f"      -> {video['title']}  ({len(video['beats'])} beats)")

    WORKDIR.mkdir(parents=True, exist_ok=True)
    scenes = []

    print("[2/5] Generating voiceover for hook, beats, and close...")

    hook_audio = str(WORKDIR / "scene_hook.mp3")
    generate_voiceover(video["hook"], hook_audio)
    scenes.append({
        "audio_path": hook_audio,
        "visual_query": video.get("hook_visual_query"),
        "caption_text": video["hook"],
        "number": None,
        "caption_position": "top",
    })

    for i, beat in enumerate(video["beats"]):
        audio_path = str(WORKDIR / f"scene_{i}.mp3")
        generate_voiceover(beat["narration"], audio_path)
        scenes.append({
            "audio_path": audio_path,
            "visual_query": beat["visual_query"],
            "caption_text": beat["narration"],
            "number": None,
            "caption_position": "bottom",
        })

    close_audio = str(WORKDIR / "scene_close.mp3")
    generate_voiceover(video["close"], close_audio)
    scenes.append({
        "audio_path": close_audio,
        "visual_query": video.get("close_visual_query", "person looking out window thinking"),
        "caption_text": video["close"],
        "number": None,
        "caption_position": "bottom",
    })

    outro_audio = str(WORKDIR / "scene_outro.mp3")
    generate_voiceover("Follow for more money stories every single day.", outro_audio)
    scenes.append({
        "audio_path": outro_audio,
        "visual_query": "city skyline aerial view night lights",
        "caption_text": "Follow for more money stories every single day.",
        "number": None,
        "caption_position": "bottom",
    })

    print(f"      -> {len(scenes)} scenes ready")

    print("[3/5] Building the video...")
    video_path = str(WORKDIR / "output.mp4")
    build_video(scenes, video_path)

    print("[4/5] Fetching trending keywords...")
    trending_keywords = get_trending_keywords(region=os.environ.get("NEWS_REGION", "US"))
    print(f"      -> {len(trending_keywords)} keywords found")

    print("[5/5] Uploading to YouTube...")
    final_meta = build_final_metadata(video, trending_keywords)
    video_id = upload_short(
        video_path=video_path,
        title=final_meta["title"],
        description=final_meta["description"],
        tags=final_meta["tags"],
    )

    print("[Cross-post] Posting to Facebook as a Reel...")
    upload_reel(video_path, final_meta["description"])

    print(json.dumps({"video_id": video_id, "title": final_meta["title"]}, indent=2))
    return video_id


if __name__ == "__main__":
    try:
        run()
    except Exception:
        print("PIPELINE FAILED:", file=sys.stderr)
        traceback.print_exc()
        sys.exit(1)
