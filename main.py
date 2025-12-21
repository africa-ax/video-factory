import os
import gdown
import json
from flask import Flask
from gtts import gTTS
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
from oauth2client.service_account import ServiceAccountCredentials
from moviepy.video.VideoClip import ImageClip
from moviepy.audio.io.AudioFileClip import AudioFileClip

app = Flask(__name__)

def upload_to_drive(filename):
    # This points to the Secret File you just uploaded to Render
    # Render puts Secret Files in the root directory by default
    json_path = 'service_account.json'
    
    scope = ['https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name(json_path, scope)
    
    gauth = GoogleAuth()
    gauth.credentials = creds
    drive = GoogleDrive(gauth)
    
    # Your specific Folder ID
    folder_id = '1jld85H4AdRm-MuJE8EmEI1cw9ZHfWRxy' 
    
    file_drive = drive.CreateFile({'title': filename, 'parents': [{'id': folder_id}]})
    file_drive.SetContentFile(filename)
    file_drive.Upload()
    return True

@app.route('/render', methods=['POST', 'GET'])
def start_render():
    try:
        # 1. DOWNLOAD INGREDIENTS
        image_url = 'https://drive.google.com/uc?id=1KNUxDRgz2c02OaB5Zu18g1dN3kfvbIdf'
        text_url = 'https://drive.google.com/uc?id=1VXH4yJl4OIAreWqrzEJQr1aoXRsokMTI'
        gdown.download(image_url, 'image.jpg', quiet=False)
        gdown.download(text_url, 'story.txt', quiet=False)
        
        with open('story.txt', 'r') as file:
            text_story = file.read().strip()

        # 2. CREATE VOICE & VIDEO
        tts = gTTS(text=text_story, lang='en')
        tts.save("voice.mp3")
        audio = AudioFileClip("voice.mp3")
        clip = ImageClip("image.jpg").set_duration(audio.duration)
        clip = clip.set_audio(audio)
        
        output_file = "final_video.mp4"
        clip.write_videofile(output_file, fps=24, codec="libx264", audio_codec="aac")
        
        # 3. UPLOAD
        upload_to_drive(output_file)
        
        return "Success! Video uploaded using Secret File.", 200
    except Exception as e:
        return f"Robot Error Detail: {str(e)}", 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=os.environ.get('PORT', 5000))
