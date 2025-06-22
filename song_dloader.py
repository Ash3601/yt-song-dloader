# Flask-based Web UI for YouTube MP3 Downloader with browser-based file download
# Requires: pip install flask yt-dlp

from flask import Flask, render_template, request, redirect, url_for, send_file, abort
import yt_dlp
import os
import tempfile

app = Flask(__name__)

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
            results.append({
                'title': entry.get('title'),
                'url': f"https://www.youtube.com/watch?v={entry.get('id')}"
            })
    return results

# def download_youtube_mp3_temp(url):
#     """
#     Downloads the MP3 to a temporary file and returns the file path.
#     """
#     temp_dir = tempfile.gettempdir()
#     ydl_opts = {
#         'format': 'bestaudio/best',
#         'noplaylist': True,
#         'postprocessors': [{
#             'key': 'FFmpegExtractAudio',
#             'preferredcodec': 'mp3',
#             'preferredquality': '192',
#         }],
#         'outtmpl': os.path.join(temp_dir, '%(title)s.%(ext)s'),
#         'prefer_ffmpeg': True,
#         'quiet': False,
#     }
#     with yt_dlp.YoutubeDL(ydl_opts) as ydl:
#         info = ydl.extract_info(url, download=True)
#         # yt-dlp may download as webm/m4a first
#         original_filename = ydl.prepare_filename(info)
#         base, _ = os.path.splitext(original_filename)
#         mp3_path = base + ".mp3"
#         if os.path.exists(mp3_path):
#             return mp3_path
#         else:
#             raise FileNotFoundError(f"MP3 file not found at expected location: {mp3_path}")

def download_youtube_mp3_temp(url):
    """
    Downloads the MP3 to a temporary file and returns the file path.
    Optimized for speed and minimal overhead.
    """
    temp_dir = tempfile.gettempdir()
    ydl_opts = {
        'format': 'bestaudio/best',
        'noplaylist': True,
        'concurrent_fragment_downloads': 5,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': os.path.join(temp_dir, '%(title)s.%(ext)s'),
        'prefer_ffmpeg': True,
        'quiet': False,
        'writethumbnail': False,
        'writeinfojson': False,
        'no_warnings': True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        original_filename = ydl.prepare_filename(info)
        base, _ = os.path.splitext(original_filename)
        mp3_path = base + ".mp3"
        if os.path.exists(mp3_path):
            return mp3_path
        else:
            raise FileNotFoundError(f"MP3 file not found at expected location: {mp3_path}")



@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        query = request.form.get('query')
        return redirect(url_for('results', q=query))
    return render_template('index.html')

@app.route('/results')
def results():
    query = request.args.get('q')
    matches = search_youtube(query)
    return render_template('results.html', query=query, results=matches)

@app.route('/download')
def download():
    url = request.args.get('url')
    try:
        mp3_path = download_youtube_mp3_temp(url)
        return send_file(mp3_path, as_attachment=True)
    except FileNotFoundError as e:
        return f"❌ Error: {e}", 404

if __name__ == '__main__':
    app.run(debug=True)