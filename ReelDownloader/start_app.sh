#!/bin/bash
echo ""
echo " ========================================"
echo "  Instagram Reels & YouTube Shorts"
echo "  Downloader  -  Starting..."
echo " ========================================"
echo ""

# Install dependencies
pip install flask yt-dlp -q 2>/dev/null || pip3 install flask yt-dlp -q 2>/dev/null

echo "  ✅  Open your browser at: http://localhost:5055"
echo "  Press Ctrl+C to stop the app."
echo ""

# Open browser in background
(sleep 2 && xdg-open "http://localhost:5055" 2>/dev/null || open "http://localhost:5055" 2>/dev/null) &

# Run app
python app.py 2>/dev/null || python3 app.py
