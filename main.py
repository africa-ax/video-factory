import os
import random
import requests
import PIL.Image
from flask import Flask, jsonify, send_file
from gtts import gTTS

# --- 1. PILLOW PATCH (Fixes ANTIALIAS Error) ---
if not hasattr(PIL.Image, 'ANTIALIAS'):
    PIL.Image.ANTIALIAS = PIL.Image.LANCZOS

from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips
# --- 2. MOVIEPY 1.0.3 AUDIO LOOP IMPORT ---
from moviepy.audio.fx.all import audio_loop

app = Flask(__name__)

# --- GITHUB CONFIGURATION ---
GITHUB_USER = "africa-ax"
REPO_NAME = "video-factory"
BRANCH = "main"
IMAGE_FOLDER = "stock_images"
RAW_URL_BASE = f"https://raw.githubusercontent.com/{GITHUB_USER}/{REPO_NAME}/{BRANCH}/{IMAGE_FOLDER}/"

@app.route("/")
def home():
    return "my-video-robot is fully fixed and running", 200

@app.route("/render", methods=["GET", "POST"])
def start_render():
    temp_files = []
    try:
        # 1. SELECT RANDOM IMAGES
        image_pool = ["1.jpg", "2.jpg", "3.jpg", "4.jpg", "5.jpg", "6.jpg"]
        selected_images = random.sample(image_pool, 4)
        clips = []

        # 2. DOWNLOAD & PROCESS IMAGES
        for img_name in selected_images:
            img_url = f"{RAW_URL_BASE}{img_name}"
            response = requests.get(img_url)
            
            if response.status_code == 200:
                temp_path = f"temp_{img_name}"
                with open(temp_path, "wb") as f:
                    f.write(response.content)
                temp_files.append(temp_path)
                
                # Set duration to 15s each for a 60s total video
                clip = ImageClip(temp_path).set_duration(15).resize(width=1280)
                clips.append(clip)

        if not clips:
            return jsonify({"error": "No images could be downloaded"}), 400

        # 3. CREATE & LOOP AUDIO
        story_text = "This construction project demonstrates our commitment to excellence and industrial innovation in every detail."
        tts = gTTS(text=story_text, lang="en")
        audio_path = "voice.mp3"
        tts.save(audio_path)
        temp_files.append(audio_path)
        
        # Load audio and use the standalone audio_loop function for v1.0.3
        raw_audio = AudioFileClip(audio_path)
        final_audio = audio_loop(raw_audio, duration=60)

        # 4. ASSEMBLE VIDEO
        final_video = concatenate_videoclips(clips, method="compose")
        final_video = final_video.set_audio(final_audio)

        output_file = "construction_video.mp4"
        final_video.write_videofile(
            output_file,
            fps=24,
            codec="libx264",
            audio_codec="aac",
            logger=None
        )

        # 5. CLEANUP
        for f in temp_files:
            if os.path.exists(f):
                os.remove(f)

        return send_file(
            output_file,
            as_attachment=True,
            download_name="construction_video.mp4",
            mimetype="video/mp4"
        )

    except Exception as e:
        for f in temp_files:
            if os.path.exists(f): os.remove(f)
        return jsonify({"status": "error", "detail": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
