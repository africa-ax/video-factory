import os
from flask import Flask, request
from gtts import gTTS
from moviepy.editor import ImageClip, AudioFileClip

app = Flask(__name__)

@app.route('/render', methods=['POST'])
def start_render():
    # 1. THE TEXT: The words you want the robot to say
    text_story = "Space is a big, silent place where stars dance forever."
    
    # 2. THE SOUND: Turning text into an mp3 file
    tts = gTTS(text=text_story, lang='en')
    tts.save("voice.mp3")
    
    # 3. THE PICTURE: Taking your uploaded image
    # (For now, we use a placeholder or your uploaded 'space.jpg')
    audio_background = AudioFileClip("voice.mp3")
    
    # Create the video using the image for the length of the audio
    # Note: You must have an image named 'image.jpg' in your repo or drive
    video = ImageClip("image.jpg").set_duration(audio_background.duration)
    video = video.set_audio(audio_background)
    
    # 4. THE OUTPUT: Save the final video
    video.write_videofile("final_video.mp4", fps=24)
    
    return "Video Factory: Success! Your video is built.", 200

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=os.environ.get('PORT', 5000))
