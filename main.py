import os
from flask import Flask
from gtts import gTTS
import gdown
from moviepy.video.VideoClip import ImageClip
from moviepy.audio.io.AudioFileClip import AudioFileClip

app = Flask(__name__)

@app.route('/render', methods=['POST', 'GET'])
def start_render():
    # 1. DOWNLOAD THE IMAGE (Using your image link)
    image_url = 'https://drive.google.com/uc?id=1KNUxDRgz2c02OaB5Zu18g1dN3kfvbIdf'
    gdown.download(image_url, 'image.jpg', quiet=False)

    # 2. DOWNLOAD THE TEXT (Using your story link)
    text_url = 'https://drive.google.com/uc?id=1VXH4yJl4OIAreWqrzEJQr1aoXRsokMTI'
    gdown.download(text_url, 'story.txt', quiet=False)
    
    # Read the words from your story.text file
    with open('story.txt', 'r') as file:
        text_story = file.read()

    # 3. CREATE THE AUDIO (Text-to-Speech)
    tts = gTTS(text=text_story, lang='en')
    tts.save("voice.mp3")
    
    # 4. ASSEMBLY (Putting it all together)
    audio_background = AudioFileClip("voice.mp3")
    video = ImageClip('image.jpg').set_duration(audio_background.duration)
    video = video.set_audio(audio_background)
    
    # 5. SAVE THE FINAL VIDEO
    video.write_videofile("final_video.mp4", fps=24, codec="libx264")
    
    return "Video Factory: Success! Your video is built.", 200

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=os.environ.get('PORT', 5000))


