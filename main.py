from flask import Flask, request, jsonify, render_template
from PIL import Image, ImageDraw, ImageFont
import subprocess
import time
import threading
import os
import uuid

app = Flask(__name__)
# Replace with your actual YouTube stream key
YOUTUBE_STREAM_KEY = '6mfq-b6w2-5f41-xhkb-fjv3'

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>YouTube Livestream Manager</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            background: linear-gradient(45deg, #ff9a9e 0%, #fad0c4 99%, #fad0c4 100%);
            min-height: 100vh;
        }
        .container {
            max-width: 800px;
            margin: auto;
            background: rgba(255, 255, 255, 0.9);
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }
        h1, h2, h3 {
            color: #333;
            text-align: center;
            margin-bottom: 30px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
        }
        .form-group {
            margin-bottom: 25px;
        }
        label {
            display: block;
            margin-bottom: 8px;
            color: #555;
            font-weight: bold;
        }
        input[type="file"] {
            display: none;
        }
        .file-upload-btn {
            display: inline-block;
            padding: 12px 20px;
            background: #4CAF50;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            transition: background 0.3s;
        }
        .file-upload-btn:hover {
            background: #45a049;
        }
        button {
            display: block;
            width: 100%;
            padding: 12px;
            margin-top: 10px;
            background: #3498db;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
            transition: background 0.3s;
        }
        button:hover {
            background: #2980b9;
        }
        #stopStream {
            background: #e74c3c;
        }
        #stopStream:hover {
            background: #c0392b;
        }
        #status {
            margin-top: 20px;
            padding: 15px;
            background-color: #f39c12;
            border-radius: 5px;
            color: white;
            font-weight: bold;
            text-align: center;
        }
        .progress-bar {
            width: 100%;
            background-color: #e0e0e0;
            padding: 3px;
            border-radius: 3px;
            box-shadow: inset 0 1px 3px rgba(0, 0, 0, .2);
            margin-top: 10px;
        }
        .progress-bar-fill {
            display: block;
            height: 22px;
            background-color: #659cef;
            border-radius: 3px;
            transition: width 500ms ease-in-out;
        }
        #changeMusicSection, #changeBackgroundSection, #videoSection {
            background: rgba(236, 240, 241, 0.8);
            padding: 20px;
            border-radius: 10px;
            margin-top: 30px;
        }
        #availableSongs {
            list-style-type: none;
            padding: 0;
        }
        #availableSongs li {
            padding: 10px;
            background-color: #ecf0f1;
            margin-bottom: 5px;
            border-radius: 5px;
            cursor: pointer;
            transition: background-color 0.3s;
        }
        #availableSongs li:hover {
            background-color: #bdc3c7;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>YouTube Livestream Manager</h1>
        <div class="form-group">
            <label for="backgroundImage">Background Image (required):</label>
            <input type="file" id="backgroundImage" accept="image/*" required>
            <label for="backgroundImage" class="file-upload-btn">Choose Background Image</label>
            <div class="progress-bar" id="backgroundProgress" style="display: none;">
                <span class="progress-bar-fill" style="width: 0%;"></span>
            </div>
        </div>
        <div class="form-group">
            <label for="musicFile">Music File (optional):</label>
            <input type="file" id="musicFile" accept="audio/*">
            <label for="musicFile" class="file-upload-btn">Choose Music File</label>
            <div class="progress-bar" id="musicProgress" style="display: none;">
                <span class="progress-bar-fill" style="width: 0%;"></span>
            </div>
        </div>
        <div class="form-group">
            <audio id="audioPlayer" controls style="width: 100%; display: none;"></audio>
        </div>
        <button id="startStream">Start Livestream</button>
        <button id="stopStream" style="display: none;">Stop Livestream</button>
        <div id="status"></div>

        <div id="videoSection" style="display: none;">
            <h2>Video Management</h2>
            <div class="form-group">
                <label for="videoFile">Video File:</label>
                <input type="file" id="videoFile" accept="video/*">
                <label for="videoFile" class="file-upload-btn">Choose Video File</label>
                <div class="progress-bar" id="videoProgress" style="display: none;">
                    <span class="progress-bar-fill" style="width: 0%;"></span>
                </div>
            </div>
            <button id="uploadVideoButton">Upload Video</button>
            <button id="playVideoButton" style="display: none;">Play Video</button>
        </div>

        <div id="changeMusicSection" style="display: none;">
            <h2>Change Music During Livestream</h2>
            <div class="form-group">
                <label for="newMusicFile">New Music File:</label>
                <input type="file" id="newMusicFile" accept="audio/*">
                <label for="newMusicFile" class="file-upload-btn">Choose New Music File</label>
                <div class="progress-bar" id="newMusicProgress" style="display: none;">
                    <span class="progress-bar-fill" style="width: 0%;"></span>
                </div>
            </div>
            <button id="changeMusicButton">Change Music</button>
            <div id="songList">
                <h3>Available Songs</h3>
                <ul id="availableSongs"></ul>
            </div>
        </div>

        <div id="changeBackgroundSection" style="display: none;">
            <h2>Change Background During Livestream</h2>
            <div class="form-group">
                <label for="newBackgroundImage">New Background Image:</label>
                <input type="file" id="newBackgroundImage" accept="image/*">
                <label for="newBackgroundImage" class="file-upload-btn">Choose New Background</label>
                <div class="progress-bar" id="newBackgroundProgress" style="display: none;">
                    <span class="progress-bar-fill" style="width: 0%;"></span>
                </div>
            </div>
            <button id="changeBackgroundButton">Change Background</button>
        </div>
    </div>

    <script>
        document.addEventListener('DOMContentLoaded', () => {
            const backgroundImage = document.getElementById('backgroundImage');
            const musicFile = document.getElementById('musicFile');
            const audioPlayer = document.getElementById('audioPlayer');
            const startStreamButton = document.getElementById('startStream');
            const stopStreamButton = document.getElementById('stopStream');
            const statusDiv = document.getElementById('status');
            const changeMusicSection = document.getElementById('changeMusicSection');
            const newMusicFile = document.getElementById('newMusicFile');
            const changeMusicButton = document.getElementById('changeMusicButton');
            const videoFile = document.getElementById('videoFile');
            const uploadVideoButton = document.getElementById('uploadVideoButton');
            const playVideoButton = document.getElementById('playVideoButton');
            const availableSongs = document.getElementById('availableSongs');
            const newBackgroundImage = document.getElementById('newBackgroundImage');
            const changeBackgroundButton = document.getElementById('changeBackgroundButton');
            const videoSection = document.getElementById('videoSection');
            const changeBackgroundSection = document.getElementById('changeBackgroundSection');

            let uploadedVideoPath = null;

            function updateProgress(progressBar, event) {
                if (event.lengthComputable) {
                    const percentComplete = (event.loaded / event.total) * 100;
                    progressBar.style.display = 'block';
                    progressBar.querySelector('.progress-bar-fill').style.width = percentComplete + '%';
                }
            }

            function uploadFile(file, url, progressBarId) {
                return new Promise((resolve, reject) => {
                    const xhr = new XMLHttpRequest();
                    const formData = new FormData();
                    formData.append('file', file);

                    xhr.open('POST', url, true);
                    xhr.upload.onprogress = (e) => updateProgress(document.getElementById(progressBarId), e);
                    xhr.onload = () => {
                        if (xhr.status === 200) {
                            resolve(JSON.parse(xhr.responseText));
                        } else {
                            reject(xhr.statusText);
                        }
                    };
                    xhr.onerror = () => reject(xhr.statusText);
                    xhr.send(formData);
                });
            }

            musicFile.addEventListener('change', (event) => {
                const file = event.target.files[0];
                if (file) {
                    const objectURL = URL.createObjectURL(file);
                    audioPlayer.src = objectURL;
                    audioPlayer.style.display = 'block';
                } else {
                    audioPlayer.src = '';
                    audioPlayer.style.display = 'none';
                }
            });

            startStreamButton.addEventListener('click', async () => {
                if (!backgroundImage.files[0]) {
                    statusDiv.textContent = 'Please select a background image.';
                    return;
                }

                try {
                    const backgroundResponse = await uploadFile(backgroundImage.files[0], '/upload_background', 'backgroundProgress');
                    let musicResponse = null;
                    if (musicFile.files[0]) {
                        musicResponse = await uploadFile(musicFile.files[0], '/upload_music', 'musicProgress');
                    }

                    const response = await fetch('/start_stream', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            backgroundPath: backgroundResponse.path,
                            musicPath: musicResponse ? musicResponse.path : null
                        }),
                    });

                    const data = await response.json();
                    statusDiv.textContent = data.message;
                    if (data.status === 'success') {
                        startStreamButton.style.display = 'none';
                        stopStreamButton.style.display = 'block';
                        changeMusicSection.style.display = 'block';
                        videoSection.style.display = 'block';
                        changeBackgroundSection.style.display = 'block';
                        updateSongList();
                    }
                } catch (error) {
                    console.error('Error:', error);
                    statusDiv.textContent = 'An error occurred while starting the stream.';
                }
            });

            stopStreamButton.addEventListener('click', async () => {
                try {
                    const response = await fetch('/stop_stream', { method: 'POST' });
                    const data = await response.json();
                    statusDiv.textContent = data.message;
                    if (data.status === 'success') {
                        startStreamButton.style.display = 'block';
                        stopStreamButton.style.display = 'none';
                        changeMusicSection.style.display = 'none';
                        videoSection.style.display = 'none';
                        changeBackgroundSection.style.display = 'none';
                    }
                } catch (error) {
                    console.error('Error:', error);
                    statusDiv.textContent = 'An error occurred while stopping the stream.';
                }
            });

            changeMusicButton.addEventListener('click', async () => {
                if (!newMusicFile.files[0]) {
                    statusDiv.textContent = 'Please select a new music file.';
                    return;
                }

                try {
                    const musicResponse = await uploadFile(newMusicFile.files[0], '/upload_music', 'newMusicProgress');
                    const response = await fetch('/change_music', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            musicPath: musicResponse.path
                        }),
                    });
                    const data = await response.json();
                    statusDiv.textContent = data.message;
                    updateSongList();
                } catch (error) {
                    console.error('Error:', error);
                    statusDiv.textContent = 'An error occurred while changing the music.';
                }
            });

            uploadVideoButton.addEventListener('click', async () => {
                if (!videoFile.files[0]) {
                    statusDiv.textContent = 'Please select a video file.';
                    return;
                }

                try {
                    const videoResponse = await uploadFile(videoFile.files[0], '/upload_video', 'videoProgress');
                    uploadedVideoPath = videoResponse.path;
                    playVideoButton.style.display = 'block';
                    statusDiv.textContent = 'Video uploaded successfully.';
                } catch (error) {
                    console.error('Error:', error);
                    statusDiv.textContent = 'An error occurred while uploading the video.';
                }
            });

            playVideoButton.addEventListener('click', async () => {
                if (!uploadedVideoPath) {
                    statusDiv.textContent = 'Please upload a video first.';
                    return;
                }

                try {
                    const response = await fetch('/play_video', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            videoPath: uploadedVideoPath
                        }),
                    });
                    const data = await response.json();
                    statusDiv.textContent = data.message;
                } catch (error) {
                    console.error('Error:', error);
                    statusDiv.textContent = 'An error occurred while playing the video.';
                }
            });

            async function updateSongList() {
                try {
                    const response = await fetch('/list_songs');
                    const data = await response.json();
                    availableSongs.innerHTML = '';
                    data.songs.forEach(song => {
                        const li = document.createElement('li');
                        li.textContent = song;
                        li.addEventListener('click', () => changeMusicTo(song));
                        availableSongs.appendChild(li);
                    });
                } catch (error) {
                    console.error('Error:', error);
                    statusDiv.textContent = 'An error occurred while fetching the song list.';
                }
            }

            async function changeMusicTo(songName) {
                try {
                    const response = await fetch('/change_music', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            musicPath: `uploads/${songName}`
                        }),
                    });
                    const data = await response.json();
                    statusDiv.textContent = data.message;
                } catch (error) {
                    console.error('Error:', error);
                    statusDiv.textContent = 'An error occurred while changing the music.';
                }
            }

            changeBackgroundButton.addEventListener('click', async () => {
                if (!newBackgroundImage.files[0]) {
                    statusDiv.textContent = 'Please select a new background image.';
                    return;
                }

                try {
                    const backgroundResponse = await uploadFile(newBackgroundImage.files[0], '/upload_background', 'newBackgroundProgress');
                    const response = await fetch('/change_background', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            backgroundPath: backgroundResponse.path
                        }),
                    });
                    const data = await response.json();
                    statusDiv.textContent = data.message;
                } catch (error) {
                    console.error('Error:', error);
                    statusDiv.textContent = 'An error occurred while changing the background.';
                }
            });

            // Call this function when the page loads
            updateSongList();
        });
    </script>
</body>
</html>
"""
# Global variables
ffmpeg_process = None
streaming = False
current_music_file = None
current_background_file = None
current_video_file = None
uploaded_files = set()  # To keep track of files uploaded during the stream
stream_url = None  # To store the stream URL

def create_start_image(message, background_path=None):
    if background_path and os.path.exists(background_path):
        img = Image.open(background_path).convert('RGB')
        img = img.resize((1280, 720), Image.LANCZOS)
    else:
        img = Image.new('RGB', (1280, 720), color=(0, 0, 0))  # Create a black image
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("arial.ttf", 40)  # Make sure you have a font file available
    except IOError:
        font = ImageFont.load_default()

    # Get the bounding box of the text
    left, top, right, bottom = draw.textbbox((0, 0), message, font=font)
    text_width = right - left
    text_height = bottom - top

    # Calculate the position to center the text
    position = ((1280 - text_width) // 2, (720 - text_height) // 2)

    # Draw the text
    draw.text(position, message, font=font, fill=(255, 255, 255))
    return img

def get_video_duration(video_path):
    result = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', video_path], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return float(result.stdout)

def stream_to_youtube(image_path, music_path=None, video_path=None):
    global current_music_file, current_video_file

    current_music_file = music_path
    current_video_file = video_path

    command = ['ffmpeg', '-re']

    if video_path and os.path.exists(video_path):
        command.extend(['-i', video_path])
        video_duration = get_video_duration(video_path)
    else:
        command.extend(['-loop', '1', '-i', image_path])
        video_duration = None

    if music_path and os.path.exists(music_path):
        command.extend(['-stream_loop', '-1', '-i', music_path])
    else:
        command.extend(['-f', 'lavfi', '-i', 'anullsrc'])

    command.extend([
        '-c:v', 'libx264',
        '-preset', 'veryfast',
        '-b:v', '3000k',
        '-c:a', 'aac',
        '-ar', '44100',
        '-b:a', '128k',
        '-pix_fmt', 'yuv420p',
        '-shortest',
        '-f', 'flv',
        f'rtmp://a.rtmp.youtube.com/live2/{YOUTUBE_STREAM_KEY}'
    ])

    process = subprocess.Popen(command)
    
    if video_duration:
        # Wait for the video to finish
        time.sleep(video_duration)
        # Restart the stream with the background image and music
        process.terminate()
        return stream_to_youtube(image_path, music_path)
    
    return process

def streaming_thread(background_path, music_path=None, video_path=None):
    global ffmpeg_process, streaming, current_background_file
    try:
        current_background_file = background_path
        start_image = create_start_image("Starting Live Stream...", background_path)
        start_image.save('current_frame.jpg')
        ffmpeg_process = stream_to_youtube('current_frame.jpg', music_path, video_path)

        while streaming:
            time.sleep(1)  # Keep the stream running
            if not ffmpeg_process.poll() is None:
                # If the process has ended (likely due to video finishing), restart with background
                ffmpeg_process = stream_to_youtube(current_background_file, current_music_file)
    except Exception as e:
        print(f"Streaming error: {str(e)}")
    finally:
        if ffmpeg_process:
            ffmpeg_process.terminate()
        streaming = False

def delete_uploaded_files():
    global uploaded_files
    for file_path in uploaded_files:
        try:
            os.remove(file_path)
            print(f"Deleted file: {file_path}")
        except OSError as e:
            print(f"Error deleting file {file_path}: {e}")
    uploaded_files.clear()

@app.route('/')
def index():
    return HTML_TEMPLATE
    
@app.route('/upload_background', methods=['POST'])
def upload_background():
    if 'file' not in request.files:
        return jsonify({'status': 'error', 'message': 'No file part'})
    file = request.files['file']
    if file.filename == '':
        return jsonify({'status': 'error', 'message': 'No selected file'})
    if file:
        filename = str(uuid.uuid4()) + os.path.splitext(file.filename)[1]
        filepath = os.path.join('uploads', filename)
        file.save(filepath)
        uploaded_files.add(filepath)  # Add to set of uploaded files
        return jsonify({'status': 'success', 'message': 'File uploaded successfully', 'path': filepath})

@app.route('/upload_music', methods=['POST'])
def upload_music():
    if 'file' not in request.files:
        return jsonify({'status': 'error', 'message': 'No file part'})
    file = request.files['file']
    if file.filename == '':
        return jsonify({'status': 'error', 'message': 'No selected file'})
    if file:
        filename = str(uuid.uuid4()) + os.path.splitext(file.filename)[1]
        filepath = os.path.join('uploads', filename)
        file.save(filepath)
        uploaded_files.add(filepath)  # Add to set of uploaded files
        return jsonify({'status': 'success', 'message': 'File uploaded successfully', 'path': filepath})

@app.route('/upload_video', methods=['POST'])
def upload_video():
    if 'file' not in request.files:
        return jsonify({'status': 'error', 'message': 'No file part'})
    file = request.files['file']
    if file.filename == '':
        return jsonify({'status': 'error', 'message': 'No selected file'})
    if file:
        filename = str(uuid.uuid4()) + os.path.splitext(file.filename)[1]
        filepath = os.path.join('uploads', filename)
        file.save(filepath)
        uploaded_files.add(filepath)  # Add to set of uploaded files
        return jsonify({'status': 'success', 'message': 'Video uploaded successfully', 'path': filepath})

@app.route('/change_background', methods=['POST'])
def change_background():
    global streaming, ffmpeg_process, current_background_file

    if not streaming:
        return jsonify({'status': 'error', 'message': 'No active stream'})

    data = request.json
    new_background_path = data.get('backgroundPath')

    if not new_background_path or not os.path.exists(new_background_path):
        return jsonify({'status': 'error', 'message': 'Invalid background image'})

    # Update the current background file
    current_background_file = new_background_path

    # Restart the stream with the new background
    if ffmpeg_process:
        ffmpeg_process.terminate()
    ffmpeg_process = stream_to_youtube(new_background_path, current_music_file, current_video_file)

    return jsonify({'status': 'success', 'message': 'Background changed successfully'})

@app.route('/play_video', methods=['POST'])
def play_video():
    global ffmpeg_process, streaming, current_video_file, current_background_file, current_music_file

    if not streaming:
        return jsonify({'status': 'error', 'message': 'No active stream'})

    data = request.json
    video_path = data.get('videoPath')

    if not video_path or not os.path.exists(video_path):
        return jsonify({'status': 'error', 'message': 'Invalid video file'})

    # Update the current video file
    current_video_file = video_path

    # Restart the stream with the video
    if ffmpeg_process:
        ffmpeg_process.terminate()
    ffmpeg_process = stream_to_youtube(current_background_file, current_music_file, video_path)

    return jsonify({'status': 'success', 'message': 'Video playback started'})

@app.route('/list_songs', methods=['GET'])
def list_songs():
    songs = [f for f in os.listdir('uploads') if f.endswith(('.mp3', '.wav', '.ogg'))]
    return jsonify({'status': 'success', 'songs': songs})

@app.route('/start_stream', methods=['POST'])
def start_stream():
    global streaming, uploaded_files, stream_url

    if streaming:
        return jsonify({'status': 'error', 'message': 'Stream is already running'})

    data = request.json
    background_path = data.get('backgroundPath')
    music_path = data.get('musicPath')

    if not background_path or not os.path.exists(background_path):
        return jsonify({'status': 'error', 'message': 'Invalid background image'})

    streaming = True
    uploaded_files = set()  # Clear the set of uploaded files
    uploaded_files.add(background_path)
    if music_path:
        uploaded_files.add(music_path)
    
    # Generate a unique stream URL (you may want to use a more sophisticated method)
    stream_url = f"https://www.youtube.com/watch?v={YOUTUBE_STREAM_KEY}"

    threading.Thread(target=streaming_thread, args=(background_path, music_path), daemon=True).start()

    return jsonify({'status': 'success', 'message': 'Livestream started successfully', 'stream_url': stream_url})

@app.route('/stop_stream', methods=['POST'])
def stop_stream():
    global streaming, ffmpeg_process, stream_url

    if not streaming:
        return jsonify({'status': 'error', 'message': 'No active stream to stop'})

    streaming = False
    if ffmpeg_process:
        ffmpeg_process.terminate()

    # Delete all uploaded files
    delete_uploaded_files()

    # Clear the stream URL
    stream_url = None

    return jsonify({'status': 'success', 'message': 'Livestream stopped successfully and uploaded files deleted'})

@app.route('/change_music', methods=['POST'])
def change_music():
    global streaming, ffmpeg_process, current_music_file

    if not streaming:
        return jsonify({'status': 'error', 'message': 'No active stream to change music'})

    data = request.json
    new_music_path = data.get('musicPath')

    if not new_music_path or not os.path.exists(new_music_path):
        return jsonify({'status': 'error', 'message': 'Invalid music file'})

    # Update the current music file
    current_music_file = new_music_path

    # Restart the stream with the new music
    if ffmpeg_process:
        ffmpeg_process.terminate()
    ffmpeg_process = stream_to_youtube(current_background_file, new_music_path, current_video_file)

    return jsonify({'status': 'success', 'message': 'Music changed successfully'})

if __name__ == '__main__':
    if not os.path.exists('uploads'):
        os.makedirs('uploads')
    app.run(debug=True)
