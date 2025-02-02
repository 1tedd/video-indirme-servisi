from flask import Flask, request, jsonify, send_file, render_template
from flask_cors import CORS
import yt_dlp
import os
import time
import re
import subprocess
import concurrent.futures

app = Flask(__name__, static_url_path='', static_folder='static')
CORS(app)

DOWNLOAD_FOLDER = "downloads"
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

current_dir = os.path.dirname(os.path.abspath(__file__))
FFMPEG_PATH = os.path.join(current_dir, "ffmpeg.exe")

def cleanup_downloads():
    try:
        for file in os.listdir(DOWNLOAD_FOLDER):
            file_path = os.path.join(DOWNLOAD_FOLDER, file)
            if time.time() - os.path.getctime(file_path) > 3600:
                os.remove(file_path)
    except Exception as e:
        print(f"Temizleme hatası: {str(e)}")

def is_youtube_url(url):
    youtube_patterns = [
        r'^https?://(?:www\.)?youtube\.com/watch\?v=[\w-]+',
        r'^https?://(?:www\.)?youtube\.com/shorts/[\w-]+',
        r'^https?://youtu\.be/[\w-]+'
    ]
    return any(re.match(pattern, url) for pattern in youtube_patterns)

def is_instagram_url(url):
    return 'instagram.com' in url.lower()

def is_tiktok_url(url):
    return 'tiktok.com' in url.lower()

def is_twitter_url(url):
    twitter_patterns = [
        r'^https?://(?:www\.)?twitter\.com/.+/status/\d+',
        r'^https?://(?:www\.)?x\.com/.+/status/\d+'
    ]
    return any(re.match(pattern, url) for pattern in twitter_patterns)

def convert_to_mp3(input_file, output_file):
    try:
        subprocess.run([
            FFMPEG_PATH,
            '-i', input_file,
            '-vn',
            '-ar', '44100',
            '-ac', '2',
            '-b:a', '320k',
            '-f', 'mp3',
            output_file
        ], check=True, capture_output=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"FFmpeg error: {e.stderr.decode()}")
        return False

def download_video(url, format_type="mp4"):
    try:
        cleanup_downloads()
        timestamp = str(int(time.time()))
        output_path = os.path.join(DOWNLOAD_FOLDER, timestamp)
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        if format_type == "mp4":
            if is_youtube_url(url):
                ydl_opts = {
                    'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
                    'outtmpl': f'{output_path}_temp.%(ext)s',
                    'ffmpeg_location': current_dir,
                    'http_headers': headers,
                    'no_check_certificate': True,
                    'concurrent_fragments': 5,
                }
            else:
                # Twitter, Instagram ve TikTok için özel ayarlar
                ydl_opts = {
                    'format': 'best',
                    'outtmpl': f'{output_path}_temp.%(ext)s',
                    'ffmpeg_location': current_dir,
                    'http_headers': headers,
                    'no_check_certificate': True,
                    'concurrent_fragments': 5,
                }
                
                # Twitter için ek ayarlar
                if is_twitter_url(url):
                    ydl_opts.update({
                        'cookies': 'twitter_cookies.txt',  # Twitter cookie dosyası
                        'format': 'best[ext=mp4]'
                    })
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                downloaded_file = ydl.prepare_filename(info)
                
                output_file = f"{output_path}.mp4"
                subprocess.run([
                    FFMPEG_PATH,
                    '-i', downloaded_file,
                    '-c:v', 'libx264',
                    '-preset', 'ultrafast',
                    '-crf', '18',
                    '-c:a', 'aac',
                    '-b:a', '192k',
                    '-movflags', '+faststart',
                    '-threads', '4',
                    output_file
                ], check=True)
                
                if os.path.exists(downloaded_file):
                    os.remove(downloaded_file)
                
                return {
                    "success": True,
                    "filename": output_file,
                    "title": info.get('title', 'Video')
                }
                
        else:  # mp3
            ydl_opts = {
                'format': 'best',
                'outtmpl': f'{output_path}_temp.%(ext)s',
                'ffmpeg_location': current_dir,
                'http_headers': headers,
                'no_check_certificate': True,
            }
            
            # Twitter için ek ayarlar
            if is_twitter_url(url):
                ydl_opts.update({
                    'cookies': 'twitter_cookies.txt',
                    'format': 'best[ext=mp4]'
                })
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                downloaded_file = ydl.prepare_filename(info)
                
                output_file = f"{output_path}.mp3"
                
                if convert_to_mp3(downloaded_file, output_file):
                    if os.path.exists(downloaded_file):
                        os.remove(downloaded_file)
                    
                    return {
                        "success": True,
                        "filename": output_file,
                        "title": info.get('title', 'Audio')
                    }
                else:
                    raise Exception("MP3 dönüştürme başarısız oldu")
                
    except Exception as e:
        print(f"Hata detayı: {str(e)}")
        return {"success": False, "error": str(e)}

@app.route('/')
def home():
    return app.send_static_file('index.html')

@app.route('/download', methods=['POST'])
def download():
    data = request.json
    url = data.get('url')
    format_type = data.get('format', 'mp4')

    if not url:
        return jsonify({"success": False, "error": "URL gerekli"})

    if not (is_youtube_url(url) or is_instagram_url(url) or 
            is_tiktok_url(url) or is_twitter_url(url)):
        return jsonify({
            "success": False, 
            "error": "Sadece YouTube, Instagram, Twitter ve TikTok linkleri desteklenmektedir"
        })

    result = download_video(url, format_type)
    
    if result["success"]:
        return jsonify({
            "success": True,
            "download_url": f"/get_file/{os.path.basename(result['filename'])}",
            "title": result["title"]
        })
    else:
        return jsonify({"success": False, "error": result["error"]})

@app.route('/get_file/<filename>')
def get_file(filename):
    try:
        file_path = os.path.join(DOWNLOAD_FOLDER, filename)
        if not os.path.exists(file_path):
            return jsonify({"success": False, "error": "Dosya bulunamadı"})
            
        return send_file(
            file_path,
            as_attachment=True,
            download_name=filename,
            mimetype='video/mp4' if filename.endswith('.mp4') else 'audio/mp3'
        )
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

if __name__ == '__main__':
    app.run(debug=True, port=5000)