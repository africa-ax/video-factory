import os
import random
import requests
import PIL.Image
from flask import Flask, jsonify, send_file
from gtts import gTTS
from uuid import uuid4

# --- PILLOW PATCH ---
if not hasattr(PIL.Image, 'ANTIALIAS'):
    PIL.Image.ANTIALIAS = PIL.Image.LANCZOS

from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips
from moviepy.audio.fx.all import audio_loop

# --- NEW GEMINI SDK (CORRECT) ---
from google import genai

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

app = Flask(__name__)

# --- GITHUB CONFIG ---
GITHUB_USER = "africa-ax"
REPO_NAME = "video-factory"
BRANCH = "main"
IMAGE_FOLDER = "stock_images"
RAW_URL_BASE = f"https://raw.githubusercontent.com/{GITHUB_USER}/{REPO_NAME}/{BRANCH}/{IMAGE_FOLDER}/"

@app.route("/")
def home():
    return "my-video-robot running with Gemini ✅", 200


def generate_script():
    seed = random.randint(1000, 999999)

    prompt = f"""
Create a UNIQUE 30-second narration for a construction video.
Seed: {seed}

Rules:
- Simple English
- Sound like a real person talking
- Mention strength, quality, and modern buildings
- Do NOT repeat ideas
- Max 75 words
"""

    response = client.models.generate_content(
        model="gemini-2.0-flash",  # ✅ CORRECT MODEL
        contents=prompt,
    )

    return response.text.strip()


@app.route("/render", methods=["GET"])
def start_render():
    temp_files = []

    try:
        # 🔹 GEMINI SCRIPT
        script_text = generate_script()

        # 🔹 RANDOM IMAGES (2 or 3)
        image_pool = ["1.jpg", "2.jpg", "3.jpg"]
        num_images = random.choice([2, 3])
        selected_images = random.sample(image_pool, num_images)
        duration_per_image = 30 / num_images

        clips = []

        for img in selected_images:
            img_url = f"{RAW_URL_BASE}{img}"
            r = requests.get(img, timeout=10)

            if r.status_code == 200:
                temp_path = f"temp_{uuid4().hex}.jpg"
                with open(temp_path, "wb") as f:
                    f.write(r.content)
                temp_files.append(temp_path)

                clip = (
                    ImageClip(temp_path)
                    .set_duration(duration_per_image)
                    .resize(width=360)  # 🔹 VERY SMALL SIZE
                )
                clips.append(clip)

        if not clips:
            return jsonify({"error": "Images failed"}), 400

        # 🔹 AUDIO
        audio_path = f"voice_{uuid4().hex}.mp3"
        gTTS(text=script_text, lang="en").save(audio_path)
        temp_files.append(audio_path)

        audio = AudioFileClip(audio_path)
        final_audio = audio_loop(audio, duration=30)

        # 🔹 VIDEO
        video = concatenate_videoclips(clips, method="compose")
        video = video.set_audio(final_audio)

        output = "construction_video.mp4"
        video.write_videofile(
            output,
            fps=24,
            codec="libx264",
            audio_codec="aac",
            preset="ultrafast",
            threads=1,
            logger=None
        )

        # 🔹 CLEANUP
        for f in temp_files:
            if os.path.exists(f):
                os.remove(f)

        return send_file(
            output,
            as_attachment=True,
            download_name="construction_video.mp4",
            mimetype="video/mp4"
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

