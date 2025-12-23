import os
import random
import requests
import PIL.Image
from flask import Flask, jsonify, send_file
from gtts import gTTS

# --- PILLOW PATCH ---
if not hasattr(PIL.Image, 'ANTIALIAS'):
    PIL.Image.ANTIALIAS = PIL.Image.LANCZOS

from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips
from moviepy.audio.fx.all import audio_loop

app = Flask(__name__)

# --- GITHUB CONFIG ---
GITHUB_USER = "africa-ax"
REPO_NAME = "video-factory"
BRANCH = "main"
IMAGE_FOLDER = "stock_images"
RAW_URL_BASE = f"https://raw.githubusercontent.com/{GITHUB_USER}/{REPO_NAME}/{BRANCH}/{IMAGE_FOLDER}/"

@app.route("/")
def home():
    return "my-video-robot running", 200

@app.route("/render", methods=["GET"])
def start_render():
    temp_files = []
    try:
        # ✅ USE ONLY 3 IMAGES
        image_pool = ["1.jpg", "2.jpg", "3.jpg"]
        selected_images = random.sample(image_pool, 3)
        clips = []

        # DOWNLOAD + PROCESS IMAGES
        for img_name in selected_images:
            img_url = f"{RAW_URL_BASE}{img_name}"
            r = requests.get(img_url, timeout=10)

            if r.status_code == 200:
                temp_path = f"temp_{img_name}"
                with open(temp_path, "wb") as f:
                    f.write(r.content)
                temp_files.append(temp_path)

                # ✅ LOW RESOLUTION + SHORT DURATION
                clip = (
                    ImageClip(temp_path)
                    .set_duration(10)     # 3 × 10s = 30s
                    .resize(width=480)    # VERY IMPORTANT
                )
                clips.append(clip)

        if not clips:
            return jsonify({"error": "Images not downloaded"}), 400

        # AUDIO (30s)
        text = "This construction project highlights precision, durability, and modern engineering excellence."
        tts = gTTS(text=text, lang="en")
        audio_path = "voice.mp3"
        tts.save(audio_path)
        temp_files.append(audio_path)

        audio = AudioFileClip(audio_path)
        final_audio = audio_loop(audio, duration=30)

        # VIDEO ASSEMBLY
        video = concatenate_videoclips(clips, method="compose")
        video = video.set_audio(final_audio)

        output = "construction_video.mp4"
        video.write_videofile(
            output,
            fps=24,
            codec="libx264",
            audio_codec="aac",
            preset="ultrafast",  # 🔥 REQUIRED
            threads=1,           # 🔥 REQUIRED
            logger=None
        )

        # CLEAN TEMP FILES
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
        for f in temp_files:
            if os.path.exists(f):
                os.remove(f)
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
