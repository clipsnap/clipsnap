from flask import Flask, render_template, request, jsonify, Response, send_from_directory
import yt_dlp
import requests
import os

app = Flask(__name__)

@app.route('/robots.txt')
def robots():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'robots.txt')

@app.route('/sitemap.xml')
def sitemap():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'sitemap.xml', mimetype='application/xml')

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/facebook')
def facebook_page():
    return render_template('facebook.html')

@app.route('/instagram')
def instagram_page():
    return render_template('instagram.html')

@app.route('/twitter')
def twitter_page():
    return render_template('twitter.html')

@app.route('/contact')
def contact_page():
    return render_template('contact.html')

@app.route('/privacy')
def privacy_page():
    return render_template('privacy.html')

@app.route('/terms')
def terms_page():
    return render_template('terms.html')

@app.route('/get-video', methods=['POST'])
def get_video():
    data = request.get_json() or {}
    url = data.get('url')
    if not url:
        return jsonify({'error': 'Please provide a valid URL.'}), 400

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
