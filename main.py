import os
import gdown
from flask import Flask, jsonify, send_file
from gtts import gTTS
from moviepy.editor import ImageClip, AudioFileClip

app = Flask(__name__)

# =============================
# HEALTH CHECK
# =============================
@app.route("/")
def home():
    return "my-video-robot is running", 200


# =============================
# RENDER VIDEO
# =============================
@app.route("/render", methods=["GET", "POST"])
def start_render():
    try:
        # 1. DOWNLOAD FILES
        image_url = "https://drive.google.com/uc?id=1KNUxDRgz2c02OaB5Zu18g1dN3kfvbIdf"
        text_url  = "https://drive.google.com/uc?id=1VXH4yJl4OIAreWqrzEJQr1aoXRsokMTI"

        gdown.download(image_url, "image.jpg", quiet=False)
        gdown.download(text_url, "story.txt", quiet=False)

        with open("story.txt", "r", encoding="utf-8") as f:
            text_story = f.read().strip()

        if not text_story:
            return jsonify({"error": "Story text is empty"}), 400

        # 2. CREATE AUDIO
        tts = gTTS(text=text_story, lang="en")
        tts.save("voice.mp3")

        audio = AudioFileClip("voice.mp3")

        # 3. CREATE VIDEO
        clip = ImageClip("image.jpg").set_duration(audio.duration)
        clip = clip.set_audio(audio)

        output_file = "final_video.mp4"

        # This ensures the file is fully written before proceeding
        clip.write_videofile(
            output_file,
            fps=24,
            codec="libx264",
            audio_codec="aac"
        )

        # 4. RETURN DOWNLOAD LINK
        return jsonify({
            "status": "rendered",
            "download_url": "/download"
        }), 200

    except Exception as e:
        return jsonify({
            "status": "error",
            "detail": str(e)
        }), 500


# =============================
# DOWNLOAD ENDPOINT
# =============================
@app.route("/download")
def download_video():
    output_file = "final_video.mp4"
    if os.path.exists(output_file):
        return send_file(
            output_file,
            as_attachment=True,
            download_name="final_video.mp4",
            mimetype="video/mp4"
        )
    else:
        return jsonify({"error": "Video not found"}), 404


# =============================
# START SERVER
# =============================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
