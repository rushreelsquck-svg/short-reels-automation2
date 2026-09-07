"""
build_video.py — The Uptick (Drama about Money)
Multi-scene format: one stock clip per scene, phrase-by-phrase captions.

Hook scene: caption at TOP of frame (caption_position="top") — larger font,
            full text shown at once for maximum first-second impact.
All other scenes: caption at BOTTOM, split into short 4-word phrases.

Background sourcing (in priority order):
  1. Pexels — with retry-backoff on 503/429
  2. Pixabay — fallback when Pexels fails
  3. Gradient — animated fallback when both fail
"""
import math
import os
import random
import textwrap
import time
from pathlib import Path

import numpy as np
import requests
from PIL import Image, ImageDraw, ImageFont

if not hasattr(Image, "ANTIALIAS"):
    Image.ANTIALIAS = Image.LANCZOS

from moviepy.editor import (
    AudioFileClip,
    CompositeAudioClip,
    CompositeVideoClip,
    ImageClip,
    VideoClip,
    VideoFileClip,
    concatenate_videoclips,
    afx,
)

ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"
FONT_PATH = ASSETS_DIR / "fonts" / "Anton-Regular.ttf"
MUSIC_DIR = ASSETS_DIR / "music"

W, H = 1080, 1920
PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY", "")
PIXABAY_API_KEY = os.environ.get("PIXABAY_API_KEY", "")
PEXELS_MAX_RETRIES = 3
PEXELS_BASE_DELAY = 4


def _split_into_phrases(text, words_per_phrase=4):
    words = text.split()
    return [" ".join(words[i:i + words_per_phrase])
            for i in range(0, len(words), words_per_phrase)] or [""]


def _render_caption_png(text, font_size=62, max_width=980):
    font = ImageFont.truetype(str(FONT_PATH), font_size)
    wrapped = textwrap.fill(text, width=20)
    lines = wrapped.split("\n")

    dummy = Image.new("RGBA", (10, 10))
    d = ImageDraw.Draw(dummy)
    line_h = max(d.textbbox((0, 0), line, font=font)[3] for line in lines) + 14
    img_h = line_h * len(lines) + 32

    img = Image.new("RGBA", (max_width, img_h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle([0, 0, max_width, img_h], radius=18, fill=(0, 0, 0, 160))

    for idx, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font)
        line_w = bbox[2] - bbox[0]
        x = (max_width - line_w) / 2
        y = 16 + idx * line_h
        draw.text((x, y), line, font=font, fill="white", stroke_width=5, stroke_fill="black")

    return np.array(img)


def _render_hook_caption_png(text, font_size=72, max_width=980):
    """Larger font for hook scene — needs to grab attention in the first second."""
    font = ImageFont.truetype(str(FONT_PATH), font_size)
    wrapped = textwrap.fill(text, width=18)
    lines = wrapped.split("\n")

    dummy = Image.new("RGBA", (10, 10))
    d = ImageDraw.Draw(dummy)
    line_h = max(d.textbbox((0, 0), line, font=font)[3] for line in lines) + 16
    img_h = line_h * len(lines) + 36

    img = Image.new("RGBA", (max_width, img_h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle([0, 0, max_width, img_h], radius=20, fill=(0, 0, 0, 185))

    for idx, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font)
        line_w = bbox[2] - bbox[0]
        x = (max_width - line_w) / 2
        y = 18 + idx * line_h
        draw.text((x, y), line, font=font, fill="white", stroke_width=6, stroke_fill="black")

    return np.array(img)


def _best_portrait_file(video_files):
    portrait = [f for f in video_files if f.get("height", 0) > f.get("width", 0)]
    candidates = portrait if portrait else video_files
    return max(candidates, key=lambda f: f.get("width", 0) * f.get("height", 0))


def _search_pexels(query, per_page=10):
    if not PEXELS_API_KEY:
        return []
    last_err = None
    for attempt in range(PEXELS_MAX_RETRIES):
        try:
            resp = requests.get(
                "https://api.pexels.com/videos/search",
                headers={"Authorization": PEXELS_API_KEY},
                params={"query": query, "orientation": "portrait", "per_page": per_page},
                timeout=15,
            )
            if resp.status_code in (429, 503):
                delay = PEXELS_BASE_DELAY * (2 ** attempt)
                print(f"Pexels {resp.status_code} on '{query}', retrying in {delay}s...")
                time.sleep(delay)
                last_err = resp.status_code
                continue
            resp.raise_for_status()
            results = resp.json().get("videos", [])
            print(f"Pexels '{query}': {len(results)} results")
            return results
        except Exception as e:
            print(f"Pexels '{query}' error: {e}")
            return []
    print(f"Pexels '{query}' gave up after {PEXELS_MAX_RETRIES} retries (last: {last_err})")
    return []


def _search_pixabay(query, per_page=10):
    if not PIXABAY_API_KEY:
        return []
    try:
        resp = requests.get(
            "https://pixabay.com/api/videos/",
            params={
                "key": PIXABAY_API_KEY,
                "q": query,
                "video_type": "film",
                "orientation": "vertical",
                "per_page": per_page,
            },
            timeout=15,
        )
        resp.raise_for_status()
        results = resp.json().get("hits", [])
        print(f"Pixabay '{query}': {len(results)} results")
        return results
    except Exception as e:
        print(f"Pixabay '{query}' error: {e}")
        return []


def _prepare_clip(local_path, duration):
    clip = VideoFileClip(local_path)
    clip = clip.resize(width=W) if (clip.h / clip.w) > (H / W) else clip.resize(height=H)
    clip = clip.crop(x_center=clip.w / 2, y_center=clip.h / 2, width=W, height=H)
    if clip.duration < duration:
        clip = concatenate_videoclips([clip] * math.ceil(duration / clip.duration))
    clip = clip.subclip(0, duration)
    clip = clip.fl_image(lambda frame: (frame * 0.58).astype("uint8"))
    return clip


def _download_pexels(video, duration):
    pick = _best_portrait_file(video["video_files"])
    local_path = f"/tmp/pexels_bg_{abs(hash(pick['link']))}.mp4"
    with requests.get(pick["link"], stream=True, timeout=60) as r:
        r.raise_for_status()
        with open(local_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
    return _prepare_clip(local_path, duration)


def _download_pixabay(hit, duration):
    videos = hit.get("videos", {})
    for quality in ("large", "medium", "small", "tiny"):
        v = videos.get(quality, {})
        if v.get("url"):
            url = v["url"]
            break
    else:
        raise ValueError("No usable video URL in Pixabay hit")
    local_path = f"/tmp/pixabay_bg_{abs(hash(url))}.mp4"
    with requests.get(url, stream=True, timeout=60) as r:
        r.raise_for_status()
        with open(local_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
    return _prepare_clip(local_path, duration)


def _fetch_clip(query, duration):
    queries = [query]
    short = " ".join(query.split()[:2])
    if short and short != query:
        queries.append(short)

    for q in queries:
        results = _search_pexels(q)
        if results:
            try:
                return _download_pexels(random.choice(results), duration)
            except Exception as e:
                print(f"Pexels download failed for '{q}': {e}")

    for q in queries:
        results = _search_pixabay(q)
        if results:
            try:
                return _download_pixabay(random.choice(results), duration)
            except Exception as e:
                print(f"Pixabay download failed for '{q}': {e}")

    print(f"All sources failed for '{query}', using gradient")
    return None


def _make_gradient_background(duration, color_a=(10, 10, 20), color_b=(40, 10, 60)):
    """Dark, moody gradient — suits the drama tone better than bright colors."""
    yy, xx = np.mgrid[0:H, 0:W]
    diag = (xx + yy) / (W + H)

    def make_frame(t):
        progress = (math.sin(t * 0.4) + 1) / 2
        mix = np.array(color_a) * (1 - progress) + np.array(color_b) * progress
        shift = 0.15 * math.sin(t * 0.6)
        frame = np.zeros((H, W, 3), dtype=np.uint8)
        for c in range(3):
            variation = 30 * np.sin(2 * math.pi * (diag + shift))
            frame[:, :, c] = np.clip(mix[c] + variation, 0, 255)
        return frame

    return VideoClip(make_frame, duration=duration)


def build_video(scenes, output_path):
    """
    scenes: list of dicts, each with:
        audio_path       — mp3 for narration
        visual_query     — stock footage search phrase (or None → gradient)
        caption_text     — narration text
        number           — int badge or None
        caption_position — "top" for hook, "bottom" for everything else
    """
    visual_clips = []
    overlay_clips = []
    audio_clips = []
    t_cursor = 0.0

    for scene in scenes:
        voice = AudioFileClip(scene["audio_path"])
        duration = voice.duration + 0.3
        audio_clips.append(voice.set_start(t_cursor))

        bg = _fetch_clip(scene["visual_query"], duration) if scene.get("visual_query") else None
        if bg is None:
            bg = _make_gradient_background(duration)
        bg = bg.set_duration(duration).resize((W, H)).set_start(t_cursor)
        visual_clips.append(bg)

        position = scene.get("caption_position", "bottom")

        if position == "top":
            # Hook: full text at once, larger font, top of frame
            png = _render_hook_caption_png(scene["caption_text"])
            cap_clip = (
                ImageClip(png)
                .set_start(t_cursor)
                .set_duration(duration)
                .set_position(("center", 80))
            )
            overlay_clips.append(cap_clip)
        else:
            # All other scenes: short phrases at bottom
            phrases = _split_into_phrases(scene["caption_text"], words_per_phrase=4)
            total_words = sum(len(p.split()) for p in phrases) or 1
            phrase_t = t_cursor
            for phrase in phrases:
                phrase_duration = max(0.5, voice.duration * (len(phrase.split()) / total_words))
                png = _render_caption_png(phrase)
                cap_h = png.shape[0]
                cap_top = max(int(H * 0.76), H - cap_h - 80)
                cap_clip = (
                    ImageClip(png)
                    .set_start(phrase_t)
                    .set_duration(phrase_duration)
                    .set_position(("center", cap_top))
                )
                overlay_clips.append(cap_clip)
                phrase_t += phrase_duration

        if scene.get("number"):
            font = ImageFont.truetype(str(FONT_PATH), 75)
            img = Image.new("RGBA", (150, 150), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            draw.ellipse([0, 0, 150, 150], fill=(230, 60, 60, 235))
            text = f"#{scene['number']}"
            bbox = draw.textbbox((0, 0), text, font=font)
            tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
            draw.text(((150 - tw) / 2, (150 - th) / 2 - bbox[1]), text, font=font, fill="white")
            badge_clip = (
                ImageClip(np.array(img))
                .set_start(t_cursor)
                .set_duration(duration)
                .set_position((40, 100))
            )
            overlay_clips.append(badge_clip)

        t_cursor += duration

    total_duration = t_cursor

    audio_tracks = list(audio_clips)
    music_files = list(MUSIC_DIR.glob("*.mp3"))
    if music_files:
        music = AudioFileClip(str(random.choice(music_files))).fx(afx.audio_loop, duration=total_duration)
        music = music.fx(afx.volumex, 0.18)
        audio_tracks.append(music)

    final_audio = CompositeAudioClip(audio_tracks).set_duration(total_duration)
    final_video = CompositeVideoClip([*visual_clips, *overlay_clips], size=(W, H)).set_duration(total_duration)
    final_video = final_video.set_audio(final_audio)

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    final_video.write_videofile(
        output_path, fps=30, codec="libx264", audio_codec="aac",
        threads=4, preset="medium", logger=None,
    )
    return output_path
