import os
import datetime
import google.generativeai as genai
from gtts import gTTS
from moviepy.editor import ImageClip, AudioFileClip

# =========================
# CONFIG
# =========================
VIDEO_COUNT = 3
IMAGE_PATH = "image.jpg"  # You must add ONE construction image to repo
OUTPUT_DIR = "outputs"

os.makedirs(OUTPUT_DIR, exist_ok=True)

# =========================
# GEMINI SETUP
# =========================
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

MODEL = genai.GenerativeModel("gemini-pro")

SYSTEM_PROMPT = """
You are a construction expert in Africa.
Your audience is beginners, home owners, and small contractors.

Generate short-form educational construction content.

Rules:
- Language: simple English
- Length: 40–60 seconds when spoken
- Start with a strong hook in the first sentence
- Focus on real construction problems, costs, mistakes, or tips
- Do not use emojis
- Do not mention AI
- End with a practical takeaway

Output format:

TITLE:
SCRIPT:
"""

# =========================
# GENERATE SCRIPT
# =========================
def generate_script():
    response = MODEL.generate_content(SYSTEM_PROMPT)
    text = response.text

    if "SCRIPT:" not in text:
        raise Exception("Invalid Gemini output")

    return text.split("SCRIPT:")[1].strip()

# =========================
# CREATE VIDEO
# =========================
def create_video(script, index):
    date_str = datetime.date.today().isoformat()
    audio_path = f"voice_{index}.mp3"
    video_path = f"{OUTPUT_DIR}/{date_str}_video_{index}.mp4"

    tts = gTTS(text=script, lang="en")
    tts.save(audio_path)

    audio = AudioFileClip(audio_path)
    clip = ImageClip(IMAGE_PATH).set_duration(audio.duration)
    clip = clip.set_audio(audio)

    clip.write_videofile(
        video_path,
        fps=24,
        codec="libx264",
        audio_codec="aac",
        logger=None
    )

    audio.close()
    clip.close()

    os.remove(audio_path)

# =========================
# MAIN
# =========================
def main():
    for i in range(1, VIDEO_COUNT + 1):
        script = generate_script()
        create_video(script, i)

    print("✅ Daily construction videos generated")

if __name__ == "__main__":
    main()
