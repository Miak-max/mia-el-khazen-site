#!/bin/sh
# Usage: ./screenshot.sh <url> <out.png> [width] [height]
# Renders a page with headless Chrome. Use a tall height for a full-page capture.
URL="${1:-http://localhost:3000/}"; OUT="${2:-shot.png}"; W="${3:-1440}"; H="${4:-900}"
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless=new --disable-gpu --hide-scrollbars \
  --window-size="$W,$H" --virtual-time-budget=6000 --screenshot="$OUT" "$URL" 2>/dev/null
echo "$OUT"
