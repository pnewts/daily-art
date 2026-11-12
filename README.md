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

## Automatic monthly search

On the 1st of each month, a GitHub Action searches YouTube (using the terms in `scripts/search_terms.txt`), asks Claude to pick about 30 great videos and write a note for each, and opens a pull request. Merge it to add the videos, or close it to skip them. It needs two repository secrets: `YOUTUBE_API_KEY` and `ANTHROPIC_API_KEY`. Videos from a batch you close without merging are saved in `rejected.json` and never proposed again.

## Daily reminder

Every morning at 8am US Pacific, a GitHub Action sends a phone notification with the day's video through the free [ntfy](https://ntfy.sh) app. It needs one repository secret: `NTFY_TOPIC` (the topic name you subscribe to in the app).

## Favorites on several devices

Tap **Copy favorites** on one device, then **Add favorites from code** on the other and paste the code. Favorites are added, never removed.
