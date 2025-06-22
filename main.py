# main.py – clean, fully‑wired version
from flask import Flask, render_template, request, redirect, url_for, send_file, session
import yt_dlp
import os
import tempfile
from ai_utils import smart_rename_title
# --- Add this import at the top ---
import ollama
import re

# ---- our helper modules ----
from cache_util import (
    get_user_id_from_cookie,
    has_user_downloaded,
    mark_user_downloaded,
    get_cached_search_results,
    cache_search_results,
    update_cached_downloaded_status,
)
from analytics_redis import (
    log_search_redis,
    log_download_redis,
)
from analytics_db import (
    log_search_db,
    log_download_db,
    get_top_searches,
    get_top_downloads,
    get_total_event_count,
)

app = Flask(__name__)
app.secret_key = "your‑secret‑key"  # mandatory for session

# -----------------------------------------------------------------------------
# helper: search YouTube (via yt‑dlp) and flag per‑user downloaded items
# -----------------------------------------------------------------------------
# def search_youtube(query: str, max_results: int = 5):
#     cached = get_cached_search_results(query)
#     if cached:
#         print(f"⚡ Using cached results for: {query}")
#         return cached

#     opts = {
#         "quiet": True,
#         "skip_download": True,
#         "extract_flat": True,
#         "force_generic_extractor": True,
#     }
#     with yt_dlp.YoutubeDL(opts) as ydl:
#         info = ydl.extract_info(f"ytsearch{max_results}:{query}", download=False)

#     user_id = get_user_id_from_cookie()
#     results = []
#     for entry in info.get("entries", []):
#         vid = entry.get("id")
#         results.append(
#             {
#                 "title": entry.get("title"),
#                 "url": f"https://www.youtube.com/watch?v={vid}",
#                 "video_id": vid,
#                 "downloaded": has_user_downloaded(user_id, vid),
#             }
#         )

#     cache_search_results(query, results)
#     return results

def search_youtube(query: str, max_results: int = 5):
    cached = get_cached_search_results(query)
    user_id = get_user_id_from_cookie()

    if cached:
        print(f"⚡ Using cached results for: {query}")
        # Inject per-user "downloaded" flag
        for result in cached:
            result["downloaded"] = has_user_downloaded(user_id, result["video_id"])
        return cached

    # Else, fetch fresh results
    opts = {
        "quiet": True,
        "skip_download": True,
        "extract_flat": True,
        "force_generic_extractor": True,
    }
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(f"ytsearch{max_results}:{query}", download=False)

    results = []
    for entry in info.get("entries", []):
        vid = entry.get("id")
        results.append(
            {
                "title": entry.get("title"),
                "url": f"https://www.youtube.com/watch?v={vid}",
                "video_id": vid,
                "downloaded": has_user_downloaded(user_id, vid),  # only when building fresh
            }
        )

    # Cache it WITHOUT the downloaded flag (user-specific)
    cache_search_results(query, [
        {
            "title": r["title"],
            "url": r["url"],
            "video_id": r["video_id"],
        } for r in results
    ])

    return results



# -----------------------------------------------------------------------------
# helper: download & convert to MP3, then log
# -----------------------------------------------------------------------------

# def download_as_mp3(url: str):
#     tmp_dir = tempfile.gettempdir()
#     opts = {
#         "format": "bestaudio/best",
#         "noplaylist": True,
#         "postprocessors": [
#             {
#                 "key": "FFmpegExtractAudio",
#                 "preferredcodec": "mp3",
#                 "preferredquality": "192",
#             }
#         ],
#         "outtmpl": os.path.join(tmp_dir, "%(title)s.%(ext)s"),
#         "prefer_ffmpeg": True,
#         "quiet": False,
#     }
#     with yt_dlp.YoutubeDL(opts) as ydl:
#         info = ydl.extract_info(url, download=True)
#         base, _ = os.path.splitext(ydl.prepare_filename(info))
#         mp3_path = base + ".mp3"

#     # per‑user + global analytics
#     user_id = get_user_id_from_cookie()
#     vid = info.get("id")
#     mark_user_downloaded(user_id, vid)
#     log_download_redis(vid)
#     log_download_db(user_id, vid)

#     if not os.path.exists(mp3_path):
#         raise FileNotFoundError("MP3 conversion failed")
#     return mp3_path
# --- Replace your current download_as_mp3 function with this one ---
def download_as_mp3(url: str):
    tmp_dir = tempfile.gettempdir()
    opts = {
        "format": "bestaudio/best",
        "noplaylist": True,
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ],
        "outtmpl": os.path.join(tmp_dir, "%(title)s.%(ext)s"),
        "prefer_ffmpeg": True,
        "quiet": False,
    }

    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)
        base, _ = os.path.splitext(ydl.prepare_filename(info))
        original_mp3_path = base + ".mp3"

    # AI‑powered renaming using Ollama (phi)
    # AI‑powered renaming using Ollama (llama2)
    try:
        original_title = info.get("title", "song")
        ai_prompt = (
            "You are a music title cleaner AI. Given a noisy or casual song title, "
            "return a single cleaned-up Indian music title with proper casing, spacing, "
            "and no emojis or slang. Output only the title.\n\n"
            f"Input: '{original_title}'"
        )
        # response = ollama.chat(
        #     model='llama2',
        #     messages=[{"role": "user", "content": ai_prompt}]
        # )
        # ai_title = response['message']['content'].strip()
        # print("AI Title from LLaMA2:", ai_title)

        # Clean filename: remove unsafe characters
        # Remove "Output:" or similar prefixes if present
        # ai_title = re.sub(r'^(Output\s*:\s*)', '', ai_title, flags=re.IGNORECASE).strip()        

        # ai_title = re.sub(r'[<>:"/\\|?*]', '', ai_title)
        ai_title = original_title
        print("Final AI title after regex:", ai_title)
        ai_mp3_path = os.path.join(tmp_dir, ai_title + ".mp3")

        os.rename(original_mp3_path, ai_mp3_path)
    except Exception as e:
        print(f"⚠️ AI rename failed, using original: {e}")
        ai_mp3_path = original_mp3_path


    # Analytics and user tracking
    user_id = get_user_id_from_cookie()
    vid = info.get("id")
    mark_user_downloaded(user_id, vid)
    log_download_redis(vid)
    log_download_db(user_id, vid)
    update_cached_downloaded_status(vid, user_id)
    # update_cached_downloaded_status(vid, user_id)

    if not os.path.exists(ai_mp3_path):
        raise FileNotFoundError("MP3 conversion failed")
    return ai_mp3_path




# -----------------------------------------------------------------------------
# routes
# -----------------------------------------------------------------------------

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        query = request.form["query"]
        return redirect(url_for("results", q=query))
    return render_template("index.html")


@app.route("/results")
def results():
    query = request.args.get("q", "")
    if not query:
        return redirect(url_for("index"))

    # log analytics
    user_id = get_user_id_from_cookie()
    log_search_redis(query)
    log_search_db(user_id, query)

    return render_template("results.html", query=query, results=search_youtube(query))


@app.route("/download")
def download():
    url = request.args.get("url")
    try:
        mp3_path = download_as_mp3(url)
        filename = os.path.basename(mp3_path)
        return send_file(mp3_path, as_attachment=True, download_name=filename, mimetype='audio/mpeg')
    except Exception as exc:
        return f"❌ Error: {exc}", 500

@app.route("/stats")
def stats():
    return render_template(
        "stats.html",
        total=get_total_event_count(),
        top_searches=get_top_searches(10),
        top_downloads=get_top_downloads(10),
    )


if __name__ == "__main__":
    app.run(debug=True)
