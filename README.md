# Daily Art

A personal web page that shows one wildly inspiring performance video a day (dance, theatre, clown, music), with a short note about the piece. You can ♥ favorites and look back at past days.

## Open it on your computer

Browsers won't load the video list from a file opened directly, so start a tiny local web server in this folder:

```bash
python3 -m http.server 8000
```

Then open http://localhost:8000 in your browser. Press `Ctrl+C` in the terminal to stop the server.

## Add a video

Add an entry to the **end** of `videos.json` (adding to the end keeps past days unchanged).
