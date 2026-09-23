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
    pattern = r'(?:v=|\/shorts\/|youtu\.be\/)([a-zA-Z0-9_-]{11})'
    match = re.search(pattern, url)
    return match.group(1) if match else None

def get_youtube_video(video_id):
    instances = [
        'https://inv.nadeko.net',
        'https://invidious.nerdvpn.de',
        'https://invidious.jing.rocks',
        'https://yt.drgnz.club'
    ]
    for base in instances:
        try:
            res = requests.get(f"{base}/api/v1/videos/{video_id}", timeout=6)
            if res.status_code == 200:
                data = res.json()
                formats = data.get('formatStreams', [])
                if formats:
                    stream = formats[-1]
                    return {
                        'title': data.get('title', 'YouTube Video'),
                        'download_url': stream.get('url'),
                        'thumbnail': f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"
                    }
        except Exception:
            continue
    return None

@app.route('/get-video', methods=['POST'])
def get_video():
    data = request.get_json() or {}
    url = data.get('url')
    if not url:
        return jsonify({'error': 'Please provide a valid URL.'}), 400

    if 'youtube.com' in url or 'youtu.be' in url:
        vid = extract_yt_id(url)
        if vid:
            yt_res = get_youtube_video(vid)
            if yt_res:
                return jsonify(yt_res)
        return jsonify({'error': 'YouTube servers temporarily busy. Please retry.'}), 503

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

    headers = {'User-Agent': 'Mozilla/5.0'}
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
