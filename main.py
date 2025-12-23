import os
import random
import requests
from flask import Flask, jsonify, send_file
from gtts import gTTS
from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips

app = Flask(__name__)

# --- GITHUB CONFIGURATION ---
GITHUB_RAW_BASE = "https://raw.githubusercontent.com/africa-ax/video-factory/main/stock_images/"
MAX_IMAGES_TO_CHECK = 100 

@app.route("/")
def home():
    return "Construction Video Bot is Running - Randomized Mode", 200

@app.route("/render", methods=["GET", "POST"])
def start_render():
    temp_files = []
    try:
        # 1. SCAN GITHUB FOR AVAILABLE IMAGES
        # This allows you to have 4 images today and 100 tomorrow without changing code
        available_images = []
        for i in range(1, MAX_IMAGES_TO_CHECK + 1):
            img_name = f"{i}.jpg"
            img_url = f"{GITHUB_RAW_BASE}{img_name}"
            # Check if the file exists on GitHub
            check = requests.head(img_url)
            if check.status_code == 200:
                available_images.append(img_name)
            elif i > 5: # Optimization: if we don't find the first few, stop early
                break

        if not available_images:
            return jsonify({"error": "No images found in your GitHub stock_images folder"}), 400

        # 2. RANDOMLY SELECT IMAGES
        # It picks up to 4 images. If you have fewer than 4, it uses all of them.
        num_to_pick = min(len(available_images), 4)
        selected_names = random.sample(available_images, num_to_pick)
        
        clips = []
        duration_per_clip = 60 / num_to_pick # Ensures total is always 60 seconds

        for name in selected_names:
            url = f"{GITHUB_RAW_BASE}{name}"
            img_data = requests.get(url).content
            
            temp_path = f"temp_{name}"
            with open(temp_path, "wb") as f:
                f.write(img_data)
            temp_files.append(temp_path)
            
            # Create clip and resize to a standard HD width (1280px)
            clip = ImageClip(temp_path).set_duration(duration_per_clip).resize(width=1280)
            clips.append(clip)

        # 3. GENERATE AUDIO
        text_story = "Welcome to our construction showcase. We are highlighting the engineering excellence and architectural precision of our latest industrial developments."
        tts = gTTS(text=text_story, lang="en")
        audio_path = "voice.mp3"
        tts.save(audio_path)
        temp_files.append(audio_path)

        # 4. ASSEMBLE FINAL VIDEO
        final_video = concatenate_videoclips(clips, method="compose")
        audio_clip = AudioFileClip(audio_path).set_duration(60)
        final_video = final_video.set_audio(audio_clip)

        output_filename = "construction_update.mp4"
        final_video.write_videofile(
            output_filename,
            fps=24,
            codec="libx264",
            audio_codec="aac",
            logger=None
        )

        # 5. CLEANUP LOCAL TEMP FILES
        for f in temp_files:
            if os.path.exists(f):
                os.remove(f)

        return send_file(
            output_filename,
            as_attachment=True,
            download_name="construction_video.mp4",
            mimetype="video/mp4"
        )

    except Exception as e:
        # Cleanup on error
        for f in temp_files:
            if os.path.exists(f):
                os.remove(f)
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
