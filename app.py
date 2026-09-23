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

def clean_youtube_url(url):
    m = re.search(r'(?:v=|\/shorts\/|youtu\.be\/)([a-zA-Z0-9_-]{11})', url)
    if m:
        return f"https://www.youtube.com/watch?v={m.group(1)}"
    return url

def fetch_youtube_video(url):
    clean_url = clean_youtube_url(url)
    
    # Engine A: Cobalt v10 standard
    try:
        r = requests.post(
            'https://api.cobalt.tools/',
            headers={
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            },
            json={'url': clean_url},
            timeout=10
        )
        if r.status_code == 200:
            data = r.json()
            dl = data.get('url')
            if dl:
                return {'title': 'YouTube Video', 'download_url': dl, 'thumbnail': ''}
    except Exception:
        pass

    # Engine B: Invidious Public Instance
    try:
        m = re.search(r'(?:v=|\/shorts\/|youtu\.be\/)([a-zA-Z0-9_-]{11})', clean_url)
        if m:
            vid = m.group(1)
            for inst in ['https://invidious.nerdvpn.de', 'https://inv.tux.pizza', 'https://yt.artemislena.eu']:
                try:
                    res = requests.get(f"{inst}/api/v1/videos/{vid}", timeout=6)
                    if res.status_code == 200:
                        vdata = res.json()
                        title = vdata.get('title', 'YouTube Video')
                        formats = vdata.get('formatStreams', [])
                        if formats:
                            return {
                                'title': title,
                                'download_url': formats[-1].get('url'),
                                'thumbnail': f"https://img.youtube.com/vi/{vid}/hqdefault.jpg"
                            }
                except Exception:
                    continue
    except Exception:
        pass

    return None

@app.route('/get-video', methods=['POST'])
def get_video():
    data = request.get_json() or {}
    url = data.get('url')
    if not url:
        return jsonify({'error': 'Please provide a valid URL.'}), 400

    if 'youtube.com' in url or 'youtu.be' in url:
        yt_res = fetch_youtube_video(url)
        if yt_res:
            return jsonify(yt_res)

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
