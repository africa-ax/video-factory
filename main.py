import os
import glob
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_file, send_from_directory
from werkzeug.utils import secure_filename
from moviepy.editor import VideoFileClip, concatenate_videoclips

app = Flask(__name__)

# Configuration
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max upload
app.config['UPLOAD_FOLDER'] = 'static'
app.config['ALLOWED_VIDEO_EXTENSIONS'] = {'mp4', 'avi', 'mov', 'mkv', 'webm'}
app.config['ALLOWED_AUDIO_EXTENSIONS'] = {'mp3', 'wav', 'ogg'}

# Ensure directories exist
for folder in ['videos', 'audio', 'output']:
    path = os.path.join(app.config['UPLOAD_FOLDER'], folder)
    os.makedirs(path, exist_ok=True)

def allowed_file(filename, file_type='video'):
    """Check if file extension is allowed"""
    if '.' not in filename:
        return False
    
    ext = filename.rsplit('.', 1)[1].lower()
    if file_type == 'video':
        return ext in app.config['ALLOWED_VIDEO_EXTENSIONS']
    elif file_type == 'audio':
        return ext in app.config['ALLOWED_AUDIO_EXTENSIONS']
    return False

@app.route('/')
def index():
    """Main page with upload and merge interface"""
    # Get list of uploaded videos
    video_files = []
    video_dir = os.path.join(app.config['UPLOAD_FOLDER'], 'videos')
    
    for file in os.listdir(video_dir):
        if allowed_file(file, 'video'):
            video_files.append({
                'name': file,
                'path': f'/static/videos/{file}',
                'size': os.path.getsize(os.path.join(video_dir, file))
            })
    
    return render_template('index.html', videos=video_files)

@app.route('/upload-video', methods=['POST'])
def upload_video():
    """Upload stock video clip"""
    if 'video' not in request.files:
        return jsonify({'error': 'No video file provided'}), 400
    
    video_file = request.files['video']
    
    if video_file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if not allowed_file(video_file.filename, 'video'):
        return jsonify({'error': 'File type not allowed'}), 400
    
    # Secure filename and save
    filename = secure_filename(video_file.filename)
    save_path = os.path.join(app.config['UPLOAD_FOLDER'], 'videos', filename)
    
    # If file exists, add timestamp
    if os.path.exists(save_path):
        name, ext = os.path.splitext(filename)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{name}_{timestamp}{ext}"
        save_path = os.path.join(app.config['UPLOAD_FOLDER'], 'videos', filename)
    
    video_file.save(save_path)
    
    return jsonify({
        'success': True,
        'filename': filename,
        'path': f'/static/videos/{filename}'
    })

@app.route('/upload-audio', methods=['POST'])
def upload_audio():
    """Upload audio file for merging"""
    if 'audio' not in request.files:
        return jsonify({'error': 'No audio file provided'}), 400
    
    audio_file = request.files['audio']
    
    if audio_file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if not allowed_file(audio_file.filename, 'audio'):
        return jsonify({'error': 'File type not allowed'}), 400
    
    # Secure filename and save
    filename = secure_filename(audio_file.filename)
    save_path = os.path.join(app.config['UPLOAD_FOLDER'], 'audio', filename)
    
    # If file exists, add timestamp
    if os.path.exists(save_path):
        name, ext = os.path.splitext(filename)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{name}_{timestamp}{ext}"
        save_path = os.path.join(app.config['UPLOAD_FOLDER'], 'audio', filename)
    
    audio_file.save(save_path)
    
    return jsonify({
        'success': True,
        'filename': filename,
        'path': f'/static/audio/{filename}'
    })

@app.route('/get-videos')
def get_videos():
    """Get list of uploaded videos"""
    video_files = []
    video_dir = os.path.join(app.config['UPLOAD_FOLDER'], 'videos')
    
    for file in os.listdir(video_dir):
        if allowed_file(file, 'video'):
            video_files.append({
                'name': file,
                'path': f'/static/videos/{file}'
            })
    
    return jsonify({'videos': video_files})

@app.route('/render', methods=['POST'])
def render_video():
    """Merge selected video clips with audio"""
    try:
        data = request.json
        selected_videos = data.get('videos', [])
        audio_filename = data.get('audio')
        
        if not selected_videos:
            return jsonify({'error': 'No videos selected'}), 400
        
        if not audio_filename:
            return jsonify({'error': 'No audio selected'}), 400
        
        # Load video clips
        clips = []
        temp_files = []
        
        for video_name in selected_videos:
            video_path = os.path.join(app.config['UPLOAD_FOLDER'], 'videos', video_name)
            
            if not os.path.exists(video_path):
                continue
            
            clip = VideoFileClip(video_path)
            # Resize to 360p width (maintain aspect ratio)
            clip = clip.resize(width=360)
            clips.append(clip)
        
        if not clips:
            return jsonify({'error': 'No valid video clips found'}), 400
        
        # Concatenate video clips
        final_clip = concatenate_videoclips(clips, method="compose")
        
        # Add audio
        audio_path = os.path.join(app.config['UPLOAD_FOLDER'], 'audio', audio_filename)
        
        if os.path.exists(audio_path):
            audio_clip = VideoFileClip(audio_path).audio
            # Set audio to video duration or loop if needed
            if audio_clip.duration < final_clip.duration:
                # Loop audio to match video length
                from moviepy.audio.fx.all import audio_loop
                audio_clip = audio_loop(audio_clip, duration=final_clip.duration)
            
            final_clip = final_clip.set_audio(audio_clip)
        
        # Generate output filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"merged_video_{timestamp}.mp4"
        output_path = os.path.join(app.config['UPLOAD_FOLDER'], 'output', output_filename)
        
        # Write video file with optimized settings for Render
        final_clip.write_videofile(
            output_path,
            fps=24,
            codec="libx264",
            audio_codec="aac",
            preset="ultrafast",
            threads=1,
            logger=None
        )
        
        # Close clips to free resources
        for clip in clips:
            clip.close()
        final_clip.close()
        
        return jsonify({
            'success': True,
            'filename': output_filename,
            'path': f'/static/output/{output_filename}',
            'download_url': f'/download/{output_filename}'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/download/<filename>')
def download_video(filename):
    """Download the rendered video"""
    output_dir = os.path.join(app.config['UPLOAD_FOLDER'], 'output')
    return send_from_directory(
        output_dir,
        filename,
        as_attachment=True,
        download_name=f"merged_video_{datetime.now().strftime('%Y%m%d')}.mp4"
    )

@app.route('/static/<path:path>')
def serve_static(path):
    """Serve static files"""
    return send_from_directory('static', path)

@app.route('/cleanup', methods=['POST'])
def cleanup():
    """Clean up old output files (optional)"""
    try:
        output_dir = os.path.join(app.config['UPLOAD_FOLDER'], 'output')
        files = os.listdir(output_dir)
        deleted_count = 0
        
        for file in files:
            file_path = os.path.join(output_dir, file)
            # Delete files older than 1 hour
            if os.path.getmtime(file_path) < (datetime.now().timestamp() - 3600):
                os.remove(file_path)
                deleted_count += 1
        
        return jsonify({'success': True, 'deleted': deleted_count})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)


