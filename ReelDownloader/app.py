import os
import sys
import re
import json
import uuid
import threading
import subprocess
from pathlib import Path
from flask import Flask, request, jsonify, send_file, send_from_directory

app = Flask(__name__, static_folder="static")

DOWNLOAD_DIR = Path("/sessions/sweet-busy-rubin/downloader/downloads")
DOWNLOAD_DIR.mkdir(exist_ok=True)

YT_DLP = "/sessions/sweet-busy-rubin/.local/bin/yt-dlp"

# Track job status
jobs = {}

def detect_platform(url: str) -> str:
    if "instagram.com" in url:
        return "instagram"
    elif "youtube.com" in url or "youtu.be" in url:
        return "youtube"
    else:
        return "unknown"

def sanitize(name: str) -> str:
    return re.sub(r'[^\w\s\-.]', '', name).strip()[:80]

def run_download(job_id: str, url: str, quality: str):
    job_dir = DOWNLOAD_DIR / job_id
    job_dir.mkdir(exist_ok=True)

    platform = detect_platform(url)
    jobs[job_id]["platform"] = platform

    # Build yt-dlp args
    cmd = [YT_DLP, "--no-playlist", "--write-info-json"]

    if platform == "youtube":
        if quality == "best":
            cmd += ["-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best"]
        else:
            cmd += ["-f", "best[height<=480][ext=mp4]/best[ext=mp4]/best"]
        cmd += ["--merge-output-format", "mp4"]
    else:
        # Instagram: just grab best available
        cmd += ["-f", "best"]

    cmd += ["-o", str(job_dir / "%(title)s.%(ext)s"), url]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120
        )

        if result.returncode != 0:
            jobs[job_id]["status"] = "error"
            jobs[job_id]["error"] = result.stderr[-600:] if result.stderr else "Unknown error"
            return

        # Find the downloaded video file
        video_files = [
            f for f in job_dir.iterdir()
            if f.suffix.lower() in (".mp4", ".webm", ".mkv", ".mov") and f.stat().st_size > 0
        ]

        # Try to get title from info json
        info_files = list(job_dir.glob("*.info.json"))
        title = "video"
        thumbnail = ""
        duration = ""
        if info_files:
            try:
                with open(info_files[0]) as f:
                    info = json.load(f)
                    title = info.get("title", "video")
                    thumbnail = info.get("thumbnail", "")
                    dur = info.get("duration")
                    if dur:
                        m, s = divmod(int(dur), 60)
                        duration = f"{m}:{s:02d}"
            except Exception:
                pass

        if not video_files:
            jobs[job_id]["status"] = "error"
            jobs[job_id]["error"] = "No video file found after download."
            return

        video_path = video_files[0]
        size_mb = round(video_path.stat().st_size / (1024 * 1024), 2)

        jobs[job_id]["status"] = "done"
        jobs[job_id]["filename"] = video_path.name
        jobs[job_id]["title"] = title
        jobs[job_id]["thumbnail"] = thumbnail
        jobs[job_id]["duration"] = duration
        jobs[job_id]["size_mb"] = size_mb
        jobs[job_id]["filepath"] = str(video_path)

    except subprocess.TimeoutExpired:
        jobs[job_id]["status"] = "error"
        jobs[job_id]["error"] = "Download timed out (>2 min). Try a shorter video."
    except Exception as e:
        jobs[job_id]["status"] = "error"
        jobs[job_id]["error"] = str(e)


@app.route("/")
def index():
    return send_from_directory("static", "index.html")


@app.route("/api/download", methods=["POST"])
def start_download():
    data = request.get_json()
    url = (data or {}).get("url", "").strip()
    quality = (data or {}).get("quality", "best")

    if not url:
        return jsonify({"error": "No URL provided"}), 400

    platform = detect_platform(url)
    if platform == "unknown":
        return jsonify({"error": "Only Instagram Reels and YouTube Shorts/videos are supported."}), 400

    job_id = str(uuid.uuid4())
    jobs[job_id] = {"status": "processing", "platform": platform}

    t = threading.Thread(target=run_download, args=(job_id, url, quality), daemon=True)
    t.start()

    return jsonify({"job_id": job_id, "platform": platform})


@app.route("/api/status/<job_id>")
def get_status(job_id):
    job = jobs.get(job_id)
    if not job:
        return jsonify({"error": "Job not found"}), 404
    return jsonify(job)


@app.route("/api/file/<job_id>")
def get_file(job_id):
    job = jobs.get(job_id)
    if not job or job.get("status") != "done":
        return jsonify({"error": "File not ready"}), 404
    filepath = job.get("filepath")
    if not filepath or not Path(filepath).exists():
        return jsonify({"error": "File missing"}), 404
    return send_file(
        filepath,
        as_attachment=True,
        download_name=job.get("filename", "video.mp4")
    )


if __name__ == "__main__":
    print("\n✅  Reel & Shorts Downloader running at http://localhost:5055\n")
    app.run(host="0.0.0.0", port=5055, debug=False)
