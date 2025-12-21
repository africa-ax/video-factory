import os
import gdown
from flask import Flask, jsonify
from gtts import gTTS
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
from oauth2client.service_account import ServiceAccountCredentials
from moviepy.editor import ImageClip, AudioFileClip

app = Flask(__name__)

# =============================
# HEALTH CHECK (stops 404)
# =============================
@app.route("/")
def home():
    return "my-video-robot is running", 200


# =============================
# GOOGLE DRIVE UPLOAD
# =============================
def upload_to_drive(filename):
    json_path = "service_account.json"

    scope = ["https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(json_path, scope)

    gauth = GoogleAuth()
    gauth.credentials = creds
    drive = GoogleDrive(gauth)

    folder_id = "1jld85H4AdRm-MuJE8EmEI1cw9ZHfWRxy"

    file_drive = drive.CreateFile({
        "title": filename,
        "parents": [{"id": folder_id}]
    })
    file_drive.SetContentFile(filename)
    file_drive.Upload()

    return True


# =============================
# RENDER VIDEO
# =============================
@app.route("/render", methods=["GET", "POST"])
def start_render():
    try:
        # 1. DOWNLOAD FILES
        image_url = "https://drive.google.com/uc?id=1KNUxDRgz2c02OaB5Zu18g1dN3kfvbIdf"
        text_url = "https://drive.google.com/uc?id=1VXH4yJl4OIAreWqrzEJQr1aoXRsokMTI"

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
        clip.write_videofile(
            output_file,
            fps=24,
            codec="libx264",
            audio_codec="aac",
            logger=None
        )

        # 4. UPLOAD TO DRIVE
        upload_to_drive(output_file)

        return jsonify({
            "status": "success",
            "message": "Video created and uploaded successfully"
        }), 200

    except Exception as e:
        return jsonify({
            "status": "error",
            "detail": str(e)
        }), 500


# =============================
# START SERVER
# =============================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
