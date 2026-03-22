import os
import re
import json
import uuid
import shutil
import threading
import subprocess
import time
from pathlib import Path
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Allow requests from GitHub Pages

DOWNLOAD_DIR = Path("/tmp/reeldownloads")
DOWNLOAD_DIR.mkdir(exist_ok=True)

# Auto-cleanup jobs older than 10 minutes
def cleanup_old_jobs():
    while True:
        time.sleep(300)
        now = time.time()
        for folder in DOWNLOAD_DIR.iterdir():
            try:
                if folder.is_dir() and (now - folder.stat().st_mtime) > 600:
                    shutil.rmtree(folder, ignore_errors=True)
            except Exception:
                pass

threading.Thread(target=cleanup_old_jobs, daemon=True).start()

jobs = {}

def detect_platform(url):
    if "instagram.com" in url:
        return "instagram"
    elif "youtube.com" in url or "youtu.be" in url:
        return "youtube"
    return "unknown"

def run_download(job_id, url, quality):
    job_dir = DOWNLOAD_DIR / job_id
    job_dir.mkdir(exist_ok=True)

    platform = detect_platform(url)
    jobs[job_id]["platform"] = platform

    yt_dlp = shutil.which("yt-dlp") or "yt-dlp"

    cmd = [yt_dlp, "--no-playlist", "--write-info-json", "--no-warnings"]

    if platform == "youtube":
        if quality == "best":
            cmd += ["-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best"]
        else:
            cmd += ["-f", "best[height<=480][ext=mp4]/best[ext=mp4]/best"]
        cmd += ["--merge-output-format", "mp4"]
    else:
        cmd += ["-f", "best[ext=mp4]/best"]

    cmd += [
        "--add-header", "User-Agent:Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "-o", str(job_dir / "%(title).60s.%(ext)s"),
        url
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)

        if result.returncode != 0:
            err = result.stderr or result.stdout or "Download failed."
            # Clean error for user display
            for line in err.splitlines():
                if "ERROR" in line or "error" in line.lower():
                    err = line.strip()
                    break
            jobs[job_id]["status"] = "error"
            jobs[job_id]["error"] = err[-300:]
            return

        video_files = sorted(
            [f for f in job_dir.iterdir()
             if f.suffix.lower() in (".mp4", ".webm", ".mkv", ".mov") and f.stat().st_size > 0],
            key=lambda f: f.stat().st_size, reverse=True
        )

        # Parse info json
        title, thumbnail, duration = "Video", "", ""
        for info_file in job_dir.glob("*.info.json"):
            try:
                with open(info_file) as f:
                    info = json.load(f)
                title = info.get("title", "Video")
                thumbnail = info.get("thumbnail", "")
                dur = info.get("duration")
                if dur:
                    m, s = divmod(int(dur), 60)
                    duration = f"{m}:{s:02d}"
            except Exception:
                pass
            break

        if not video_files:
            jobs[job_id]["status"] = "error"
            jobs[job_id]["error"] = "No video found. The URL may be private or unsupported."
            return

        vf = video_files[0]
        jobs[job_id].update({
            "status": "done",
            "filename": vf.name,
            "filepath": str(vf),
            "title": title,
            "thumbnail": thumbnail,
            "duration": duration,
            "size_mb": round(vf.stat().st_size / (1024 * 1024), 2),
        })

    except subprocess.TimeoutExpired:
        jobs[job_id]["status"] = "error"
        jobs[job_id]["error"] = "Timed out. Try a shorter video or check your URL."
    except Exception as e:
        jobs[job_id]["status"] = "error"
        jobs[job_id]["error"] = str(e)


@app.route("/")
def health():
    return jsonify({"status": "ok", "service": "ReelSave API"})


@app.route("/api/download", methods=["POST"])
def start_download():
    data = request.get_json(silent=True) or {}
    url = data.get("url", "").strip()
    quality = data.get("quality", "best")

    if not url:
        return jsonify({"error": "No URL provided."}), 400

    platform = detect_platform(url)
    if platform == "unknown":
        return jsonify({"error": "Only Instagram Reels and YouTube Shorts/videos are supported."}), 400

    job_id = str(uuid.uuid4())
    jobs[job_id] = {"status": "processing", "platform": platform}

    threading.Thread(target=run_download, args=(job_id, url, quality), daemon=True).start()
    return jsonify({"job_id": job_id, "platform": platform})


@app.route("/api/status/<job_id>")
def job_status(job_id):
    job = jobs.get(job_id)
    if not job:
        return jsonify({"error": "Job not found"}), 404
    # Don't send filepath to client
    safe = {k: v for k, v in job.items() if k != "filepath"}
    return jsonify(safe)


@app.route("/api/file/<job_id>")
def serve_file(job_id):
    job = jobs.get(job_id)
    if not job or job.get("status") != "done":
        return jsonify({"error": "File not ready"}), 404
    fp = job.get("filepath")
    if not fp or not Path(fp).exists():
        return jsonify({"error": "File missing or expired"}), 404

    response = send_file(fp, as_attachment=True, download_name=job.get("filename", "video.mp4"))

    # Schedule file deletion after serving
    def delete_later():
        time.sleep(30)
        shutil.rmtree(Path(fp).parent, ignore_errors=True)
        jobs.pop(job_id, None)

    threading.Thread(target=delete_later, daemon=True).start()
    return response


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5055))
    app.run(host="0.0.0.0", port=port)
