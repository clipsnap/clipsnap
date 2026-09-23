from flask import Flask, render_template, request, jsonify, Response
import yt_dlp
import requests

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/instagram')
def instagram():
    return render_template('instagram.html')

@app.route('/youtube')
def youtube():
    return render_template('youtube.html')

@app.route('/twitter')
def twitter():
    return render_template('twitter.html')

@app.route('/get-video', methods=['POST'])
def get_video():
    data = request.get_json() or {}
    url = data.get('url', '').strip()

    if not url:
        return jsonify({'error': 'Please provide a valid video link.'}), 400

    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'extractor_args': {'youtube': {'player_client': ['android', 'web']}},
        'user_agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Mobile Safari/537.36',
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            video_url = None
            if 'formats' in info:
                valid_formats = [f for f in info['formats'] if f.get('url') and f.get('vcodec') != 'none' and f.get('acodec') != 'none']
                if valid_formats:
                    video_url = valid_formats[-1]['url']
                else:
                    for f in reversed(info['formats']):
                        if f.get('url') and f.get('vcodec') != 'none':
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
        return jsonify({'error': 'Could not process this link.'}), 500

@app.route('/download-file')
def download_file():
    video_url = request.args.get('url')
    if not video_url:
        return "Missing URL", 400

    headers = {
        'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Mobile Safari/537.36',
        'Accept': '*/*',
        'Range': 'bytes=0-'
    }

    if 'tiktok' in video_url or 'byteoversea' in video_url:
        headers['Referer'] = 'https://www.tiktok.com/'
    elif 'instagram' in video_url or 'cdninstagram' in video_url or 'fbcdn' in video_url:
        headers['Referer'] = 'https://www.instagram.com/'
    elif 'googlevideo' in video_url or 'youtube' in video_url:
        headers['Referer'] = 'https://www.youtube.com/'

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
