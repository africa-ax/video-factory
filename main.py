import os
import gdown
from flask import Flask, jsonify, send_file
from gtts import gTTS
from moviepy.editor import ImageClip, AudioFileClip

app = Flask(__name__)

VIDEO_PATH = "final_video.mp4"

@app.route("/")
def home():
    return "my-video-robot is running", 200


# =============================
# STEP 1: RENDER VIDEO
# =============================
@app.route("/render", methods=["GET"])
def start_render():
    try:
        image_url = "https://drive.google.com/uc?id=1KNUxDRgz2c02OaB5Zu18g1dN3kfvbIdf"
        text_url = "https://drive.google.com/uc?id=1VXH4yJl4OIAreWqrzEJQr1aoXRsokMTI"

        gdown.download(image_url, "image.jpg", quiet=True)
        gdown.download(text_url, "story.txt", quiet=True)

        with open("story.txt", "r", encoding="utf-8") as f:
            text_story = f.read().strip()

        if not text_story:
            return jsonify({"error": "Story empty"}), 400

        tts = gTTS(text=text_story, lang="en")
        tts.save("voice.mp3")

        audio = AudioFileClip("voice.mp3")
        clip = ImageClip("image.jpg").set_duration(audio.duration)
        clip = clip.set_audio(audio)

        clip.write_videofile(
            VIDEO_PATH,
            fps=24,
            codec="libx264",
            audio_codec="aac",
            logger=None
        )

        return jsonify({
            "status": "rendered",
            "download_url": "/download"
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# =============================
# STEP 2: DOWNLOAD VIDEO
# =============================
@app.route("/download", methods=["GET"])
def download_video():
    if not os.path.exists(VIDEO_PATH):
        return jsonify({"error": "Video not ready"}), 404

    return send_file(
        VIDEO_PATH,
        as_attachment=True,
        download_name="final_video.mp4",
        mimetype="video/mp4"
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
