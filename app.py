from flask import Flask, render_template, request, jsonify, Response
import yt_dlp
import requests
import re

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/youtube')
def youtube_page():
    return render_template('youtube.html')

@app.route('/instagram')
def instagram_page():
    return render_template('instagram.html')

@app.route('/twitter')
def twitter_page():
    return render_template('twitter.html')

def extract_yt_id(url):
    m = re.search(r'(?:v=|\/shorts\/|youtu\.be\/)([a-zA-Z0-9_-]{11})', url)
    return m.group(1) if m else None

def get_direct_yt_stream(video_id):
    # Public fast resolver gateway
    apis = [
        f"https://co.wuk.sh/api/json",
        f"https://api.cobalt.tools/api/json"
    ]
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'User-Agent': 'Mozilla/5.0'
    }
    target_url = f"https://www.youtube.com/watch?v={video_id}"

    for api in apis:
        try:
            r = requests.post(api, json={'url': target_url}, headers=headers, timeout=8)
            if r.status_code == 200:
                res = r.json()
                if res.get('url'):
                    return {
                        'title': 'YouTube Video',
                        'download_url': res.get('url'),
                        'thumbnail': f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"
                    }
        except Exception:
            continue

    # Fallback to direct mp4 link resolver
    try:
        r2 = requests.get(f"https://y-api.org/api/v1/info/{video_id}", timeout=8)
        if r2.status_code == 200:
            res2 = r2.json()
            if res2.get('download_url'):
                return {
                    'title': res2.get('title', 'YouTube Video'),
                    'download_url': res2.get('download_url'),
                    'thumbnail': f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"
                }
    except Exception:
        pass

    return None

@app.route('/get-video', methods=['POST'])
def get_video():
    data = request.get_json() or {}
    url = data.get('url')
    if not url:
        return jsonify({'error': 'Please provide a valid URL.'}), 400

    # Handle YouTube separately to avoid bot block
    if 'youtube.com' in url or 'youtu.be' in url:
        vid = extract_yt_id(url)
        if vid:
            yt_data = get_direct_yt_stream(vid)
            if yt_data:
                return jsonify(yt_data)
        return jsonify({'error': 'Could not process this YouTube link. Please try another.'}), 500

    # Keep yt-dlp for Instagram and Twitter (Working)
    ydl_opts = {
        'format': 'best[ext=mp4]/best',
        'quiet': True,
        'no_warnings': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            video_url = None
            if 'formats' in info:
                for f in reversed(info['formats']):
                    if f.get('ext') == 'mp4' and f.get('acodec') != 'none' and f.get('vcodec') != 'none':
                        video_url = f.get('url')
                        break
            if not video_url:
                video_url = info.get('url')

            return jsonify({
                'title': info.get('title', 'Social Video'),
                'download_url': video_url,
                'thumbnail': info.get('thumbnail', '')
            })
    except Exception as e:
        print("Backend error:", e)
        return jsonify({'error': 'Could not process this link.'}), 500

@app.route('/download-file')
def download_file():
    video_url = request.args.get('url')
    if not video_url:
        return "Missing URL", 400

    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    try:
        req = requests.get(video_url, headers=headers, stream=True, timeout=30)
        return Response(
            req.iter_content(chunk_size=1024 * 128),
            content_type=req.headers.get('Content-Type', 'video/mp4'),
            headers={'Content-Disposition': 'attachment; filename="video.mp4"'}
        )
    except Exception as err:
        return f"Stream error: {str(err)}", 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
