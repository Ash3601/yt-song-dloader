# main.py
from flask import Flask, render_template, request, redirect, url_for, send_file, abort, session
import yt_dlp
import os
import tempfile
import redis

# Use SQLite-based analytics now
from analyticsdb import log_search, log_download, get_top_searches, get_top_downloads
from user_session import get_or_create_user_id, mark_downloaded, has_downloaded

app = Flask(__name__)
app.secret_key = 'your-secure-random-key'
r = redis.Redis()

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        query = request.form.get('query')
        return redirect(url_for('results', q=query))
    return render_template('index.html')

def search_youtube(query: str, max_results=5):
    ydl_opts = {
        'quiet': True,
        'skip_download': True,
        'extract_flat': True,
        'force_generic_extractor': True,
    }
    results = []
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(f"ytsearch{max_results}:{query}", download=False)
        for entry in info.get('entries', []):
            video_id = entry.get('id')
            is_downloaded = has_downloaded(video_id, r)
            results.append({
                'title': entry.get('title'),
                'url': f"https://www.youtube.com/watch?v={video_id}",
                'downloaded': is_downloaded
            })
    return results

@app.route('/results')
def results():
    query = request.args.get('q')
    log_search(query)
    matches = search_youtube(query)
    return render_template('results.html', query=query, results=matches)

def download_youtube_mp3_temp(url):
    temp_dir = tempfile.gettempdir()
    ydl_opts = {
        'format': 'bestaudio/best',
        'noplaylist': True,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': os.path.join(temp_dir, '%(title)s.%(ext)s'),
        'prefer_ffmpeg': True,
        'quiet': False,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        video_id = info.get("id")
        mark_downloaded(video_id, r)
        log_download(video_id)
        base_path = os.path.splitext(ydl.prepare_filename(info))[0]
        mp3_path = base_path + ".mp3"
        if os.path.exists(mp3_path):
            return mp3_path
        else:
            raise FileNotFoundError(f"MP3 not found: {mp3_path}")

@app.route('/download')
def download():
    url = request.args.get('url')
    try:
        mp3_path = download_youtube_mp3_temp(url)
        return send_file(mp3_path, as_attachment=True)
    except FileNotFoundError as e:
        return f"❌ Error: {e}", 404

@app.route('/stats')
def stats():
    top_searches = get_top_searches(10)
    top_downloads = get_top_downloads(10)
    return render_template("stats.html", searches=top_searches, downloads=top_downloads)

if __name__ == '__main__':
    app.run(debug=True)
