"""
build_video.py — The Uptick (Drama, AI images)
Ken Burns zoom/pan animation on AI-generated images.
Hook: caption TOP, large font. Other scenes: caption BOTTOM, short phrases.
"""
import math
import os
import random
import textwrap
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

if not hasattr(Image, "ANTIALIAS"):
    Image.ANTIALIAS = Image.LANCZOS

from moviepy.editor import (
    AudioFileClip,
    CompositeAudioClip,
    CompositeVideoClip,
    ImageClip,
    VideoClip,
    afx,
)

ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"
FONT_PATH = ASSETS_DIR / "fonts" / "Anton-Regular.ttf"
MUSIC_DIR = ASSETS_DIR / "music"

W, H = 1080, 1920


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
    draw.rounded_rectangle([0, 0, max_width, img_h], radius=18, fill=(0, 0, 0, 170))
    for idx, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font)
        line_w = bbox[2] - bbox[0]
        x = (max_width - line_w) / 2
        y = 16 + idx * line_h
        draw.text((x, y), line, font=font, fill="white", stroke_width=5, stroke_fill="black")
    return np.array(img)


def _render_hook_caption_png(text, font_size=72, max_width=980):
    font = ImageFont.truetype(str(FONT_PATH), font_size)
    wrapped = textwrap.fill(text, width=18)
    lines = wrapped.split("\n")
    dummy = Image.new("RGBA", (10, 10))
    d = ImageDraw.Draw(dummy)
    line_h = max(d.textbbox((0, 0), line, font=font)[3] for line in lines) + 16
    img_h = line_h * len(lines) + 36
    img = Image.new("RGBA", (max_width, img_h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle([0, 0, max_width, img_h], radius=20, fill=(0, 0, 0, 190))
    for idx, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font)
        line_w = bbox[2] - bbox[0]
        x = (max_width - line_w) / 2
        y = 18 + idx * line_h
        draw.text((x, y), line, font=font, fill="white", stroke_width=6, stroke_fill="black")
    return np.array(img)


def _ken_burns_clip(image_path, duration, zoom_in=True, pan_right=True):
    img = Image.open(image_path).convert("RGB")
    src_w, src_h = img.size
    target_ratio = W / H
    src_ratio = src_w / src_h
    if src_ratio > target_ratio:
        new_w = int(src_h * target_ratio)
        x0 = (src_w - new_w) // 2
        img = img.crop((x0, 0, x0 + new_w, src_h))
    else:
        new_h = int(src_w / target_ratio)
        y0 = (src_h - new_h) // 2
        img = img.crop((0, y0, src_w, y0 + new_h))
    base_w, base_h = img.size
    zoom_start, zoom_end = (1.0, 1.12) if zoom_in else (1.12, 1.0)

    def make_frame(t):
        progress = t / duration if duration > 0 else 0
        zoom = zoom_start + (zoom_end - zoom_start) * progress
        crop_w = max(1, int(base_w / zoom))
        crop_h = max(1, int(base_h / zoom))
        max_x_off = base_w - crop_w
        max_y_off = base_h - crop_h
        pan_progress = progress if pan_right else (1 - progress)
        x0 = int(max_x_off * pan_progress)
        y0 = int(max_y_off * 0.5)
        cropped = img.crop((x0, y0, x0 + crop_w, y0 + crop_h))
        resized = cropped.resize((W, H), Image.LANCZOS)
        return np.array(resized)

    return VideoClip(make_frame, duration=duration)


def build_video(scenes, output_path):
    visual_clips = []
    overlay_clips = []
    audio_clips = []
    t_cursor = 0.0
    zoom_in = True
    pan_right = True

    for scene in scenes:
        voice = AudioFileClip(scene["audio_path"])
        duration = voice.duration + 0.3
        audio_clips.append(voice.set_start(t_cursor))

        bg = _ken_burns_clip(scene["image_path"], duration, zoom_in=zoom_in, pan_right=pan_right)
        bg = bg.set_start(t_cursor)
        visual_clips.append(bg)
        zoom_in = not zoom_in
        pan_right = not pan_right

        position = scene.get("caption_position", "bottom")

        if position == "top":
            png = _render_hook_caption_png(scene["caption_text"])
            cap_clip = (
                ImageClip(png)
                .set_start(t_cursor)
                .set_duration(duration)
                .set_position(("center", 80))
            )
            overlay_clips.append(cap_clip)
        else:
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
