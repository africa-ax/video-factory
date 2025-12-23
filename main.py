import os
import random
import requests
from flask import Flask, jsonify, send_file
from gtts import gTTS
from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips

app = Flask(__name__)

# --- CONFIGURATION BASED ON YOUR SCREENSHOT ---
# This points to your specific GitHub folder
GITHUB_USER = "africa-ax"
REPO_NAME = "video-factory"
BRANCH = "main"
IMAGE_FOLDER = "stock_images"

# The base URL for raw files from your repository
RAW_URL_BASE = f"https://raw.githubusercontent.com/{GITHUB_USER}/{REPO_NAME}/{BRANCH}/{IMAGE_FOLDER}/"

@app.route("/")
def home():
    return "my-video-robot is running on Render", 200

@app.route("/render", methods=["GET", "POST"])
def start_render():
    temp_files = []
    try:
        # 1. DEFINE IMAGE POOL
        # Since we can't 'list' a GitHub folder directly via URL, 
        # ensure your images are named numerically (1.jpg, 2.jpg, etc.)
        # or list them manually here:
        image_pool = ["1.jpg", "2.jpg", "3.jpg", "4.jpg", "5.jpg", "6.jpg"]
        
        # Pick 4 random images from your stock_images folder
        selected_images = random.sample(image_pool, 4)
        clips = []

        # 2. DOWNLOAD AND PROCESS IMAGES
        for img_name in selected_images:
            img_url = f"{RAW_URL_BASE}{img_name}"
            response = requests.get(img_url)
            
            if response.status_code == 200:
                temp_path = f"temp_{img_name}"
                with open(temp_path, "wb") as f:
                    f.write(response.content)
                temp_files.append(temp_path)
                
                # Each image lasts 15 seconds (4 images * 15s = 60s total)
                clip = ImageClip(temp_path).set_duration(15)
                # Ensure all images are resized to a standard width for the video
                clip = clip.resize(width=1280) 
                clips.append(clip)

        if not clips:
            return jsonify({"error": "No images could be downloaded. Check image names."}), 400

        # 3. CREATE AUDIO (1 Minute Story)
        story_text = "This construction project demonstrates our commitment to excellence and industrial innovation in every detail."
        tts = gTTS(text=story_text, lang="en")
        audio_path = "voice.mp3"
        tts.save(audio_path)
        temp_files.append(audio_path)
        
        audio_clip = AudioFileClip(audio_path).set_duration(60)

        # 4. ASSEMBLE VIDEO
        final_clip = concatenate_videoclips(clips, method="compose")
        final_clip = final_clip.set_audio(audio_clip)

        output_file = "construction_video.mp4"
        final_clip.write_videofile(
            output_file,
            fps=24,
            codec="libx264",
            audio_codec="aac",
            logger=None
        )

        # 5. CLEANUP LOCAL TEMP FILES
        for f in temp_files:
            if os.path.exists(f):
                os.remove(f)

        # 6. RETURN FILE
        return send_file(
            output_file,
            as_attachment=True,
            download_name="construction_video.mp4",
            mimetype="video/mp4"
        )

    except Exception as e:
        # Emergency cleanup
        for f in temp_files:
            if os.path.exists(f): os.remove(f)
        return jsonify({"status": "error", "detail": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)


