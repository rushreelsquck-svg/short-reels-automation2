"""
generate_audio.py
Free text-to-speech voiceover using gTTS (Google Translate's TTS endpoint).
It's serviceable but robotic. For a noticeably better voice, swap this out for
ElevenLabs or Azure TTS (both have simple REST APIs) — see README "Upgrades".
"""
from pathlib import Path

from gtts import gTTS


def generate_voiceover(script_text: str, output_path: str) -> str:
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    tts = gTTS(text=script_text, lang="en", slow=False)
    tts.save(output_path)
    return output_path


if __name__ == "__main__":
    generate_voiceover("This is a test of the voiceover system.", "/tmp/test_audio.mp3")
    print("Saved /tmp/test_audio.mp3")
