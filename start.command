#!/bin/bash
# Earth Trend Detective: serves this folder and opens the globe. Close this window to stop it.
cd "$(dirname "$0")"
( sleep 1; open "http://localhost:3220/" ) &
python3 -m http.server 3220
