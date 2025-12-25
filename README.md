# Video Merger App

A simple Flask application that allows you to upload stock video clips and merge them with audio to create a single video file.

## Features

- Upload multiple stock video clips (MP4, AVI, MOV, MKV, WEBM)
- Upload audio files (MP3, WAV, OGG)
- Select specific videos from your uploaded library
- Merge selected videos with audio into a single video
- Download the final merged video
- Responsive web interface

## Deployment on Render

1. **Create a new Web Service on Render**
   - Connect your GitHub repository
   - Select Python as the runtime
   - Use the following settings:
     - **Build Command:** `pip install -r requirements.txt`
     - **Start Command:** `python main.py`

2. **Environment Variables**
   - No environment variables required for basic functionality

3. **Important Notes for Render:**
   - File storage is ephemeral (files will be lost on redeploy)
   - For persistent storage, consider using Render Disk or external storage (S3)
   - Video processing requires ffmpeg (automatically installed via moviepy)

## Local Development

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
