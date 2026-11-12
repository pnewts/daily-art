# CLAUDE.md

Read this file before starting any task. Keep it up to date.

## Project overview

A personal app that shows me **one new video a day of a wildly inspiring piece of art**, mostly performance: theatre, dance, clowning, physical theatre and music.

- **Who uses it:** Just me
- **Platform:** a web page (works on phone and computer)
- **Live site:** https://pnewts.github.io/daily-art/

### The kind of art I'm after

These artists set the tone. Use them as a guide when choosing or suggesting videos:

- Philippe Gaulier (clown, bouffon, theatre teaching)
- Damien Jalet (choreography)
- Pina Bausch (Tanztheater / dance theatre)
- Philip Glass (minimalist music, opera)
- SITI Company (ensemble theatre, Viewpoints)
- Spymonkey (physical comedy theatre)

Aim for work that is bold, surprising, physical and moving, not just technically good.

### Core behavior

- Each day, show one video I haven't seen before.
- The same video stays up all day, and a new one appears the next day.

- Each video has a short note about the artist and piece.
- I can ♥ favorites and look back at past days.

### How it works

- `videos.json` is the hand-picked list. The day number since `START_DATE` (in `app.js`) picks the video, and the list repeats when it runs out. **Always add new videos to the end** so past days don't change.
- Videos are embeds of public YouTube (or Vimeo) videos. Before adding one, check it allows embedding: `https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v=VIDEO_ID&format=json` returns 200 if it does, and 401 if embedding is blocked (e.g. DV8 blocks all of theirs). Never guess video IDs.
- Favorites and history are saved in the browser (`localStorage`), so each device keeps its own copy.
- To move favorites to another device: "Copy favorites" makes a code like `daily-art:bausch-vollmond,jalet-skid`; "Add favorites from code" on the other device **merges** it in (never removes, ignores unknown IDs).
- Testing tricks: `?date=YYYY-MM-DD` pretends it's another day; `?video=<id>` shows a specific video.
- Hosted on GitHub Pages from the root of the `main` branch. Anything pushed to `main` goes live within a minute or two. Keep file paths relative (`style.css`, not `/style.css`), because the site lives under `/daily-art/`.

### Automatic monthly search

- `.github/workflows/find-videos.yml` runs on GitHub on the 1st of each month (or on demand: Actions → "Find new videos" → "Run workflow").
- It runs `scripts/find_videos.py`, which:
  1. searches YouTube (Data API) for every line in `scripts/search_terms.txt`;
  2. drops known, non-embeddable, very short (<1 min), very long (>3 h) and obscure (<1,000 views) videos;
  3. asks Claude (`claude-opus-5-5`, via the `anthropic` Python library, pinned in the workflow) to pick up to 30 and write notes. Claude also gets the list of pieces already in `videos.json` and is told not to pick another video of the same piece;
  4. appends them to the end of `videos.json` with `"source": "auto"` and `"id": "yt-<youtubeId>"`.
- The workflow then opens a pull request; I merge or close it. Nothing is added without my OK.
- Keys live only in GitHub secrets: `YOUTUBE_API_KEY` and `ANTHROPIC_API_KEY`. Never put them in files.
- To test the script without real keys, stub `youtube_get` and `anthropic.Anthropic` (don't call the real APIs from a session).
- **Rejected videos:** `rejected.json` lists YouTube IDs never to propose again. When I close a `new-videos-*` pull request without merging, `.github/workflows/remember-rejected.yml` runs `scripts/remember_rejected.py` and adds that batch's videos to it. `find_videos.py` skips everything in it.
- When Claude removes videos from a batch by hand, also add them to `rejected.json`.

### Daily reminder

- `.github/workflows/daily-reminder.yml` runs `scripts/notify.py` every morning and sends a phone notification through ntfy (free app) with that day's title. Tapping it opens the live site.
- 8am US Pacific: GitHub's timer is UTC-only, so it runs at 15:05 and 16:05 UTC and the script only sends during the 8 o'clock hour in `America/Los_Angeles`. A manual "Run workflow" always sends (for testing).
- The ntfy topic name lives in the GitHub secret `NTFY_TOPIC`, not in the code.
- `notify.py` reads `START_DATE` from `app.js` and uses the same rule as the page to pick the day's video. Keep them in step.

### Next steps / open questions

- Nothing planned right now.

## How to work with me

- I'm a beginner. Explain what you're doing and why in plain language. Avoid jargon, or define it when you use it.
- Check with me before big changes, like adding a library, restructuring the project, or deleting files.
- When I need to run something, give me the exact command and tell me what I should see if it worked.
- If something goes wrong, tell me plainly what happened and what you suggest next.
- The repo is public: never commit passwords, API keys or personal info.

## Core rule: keep it simple

- Pick the simplest approach that works.
- Don't add libraries, frameworks, or abstractions unless they're clearly needed.
- Work in small steps. Get something working before adding more.
- Write readable code with short comments, not clever code.

## Tech stack

Plain HTML, CSS and JavaScript (`index.html`, `style.css`, `app.js`, `videos.json`). No frameworks, no build step, nothing to install. Chosen because it's the simplest thing that works, and easy for a beginner to read.

## Commands

- **Install:** nothing
- **Run:** `python3 -m http.server 8000`, then open http://localhost:8000
- **Test:** open the page with different `?date=` values, check the video changes, ♥ works, and Past days fills in. Check phone width too.

## Decisions log

Add key decisions here (newest last) so future sessions know what we decided and why.

- 2026-11-12: Created this file.
- 2026-11-12: App idea: a daily inspiring performance-art video (see Project overview).
- 2026-11-12: Web page, built with plain HTML/CSS/JS.
- 2026-11-12: Videos are a hand-picked list first (30 videos to start); automatic search comes later ("mix of both").
- 2026-11-12: Each video gets a short note; favorites and history are kept in browser storage.
- 2026-11-12: Created a cloud environment called "daily-art" that can reach www.youtube.com and vimeo.com, so video links can be checked.
- 2026-11-12: Hosted on GitHub Pages (repo made public; it holds no secrets or personal data). Live at https://pnewts.github.io/daily-art/.
- 2026-11-12: Automatic search: monthly GitHub Action, ~30 videos, Claude writes the notes, and I approve each batch as a pull request. The script is Python (runs on GitHub only; the web page stays plain HTML/CSS/JS).
- 2026-11-12: Workflow uses actions/checkout@v7 and actions/setup-python@v7 (Node.js 24 versions) after GitHub warned that Node.js 20 is deprecated.
- 2026-11-12: Daily reminder at 8am US Pacific via ntfy (no account needed), sent by a GitHub Action.
- 2026-11-12: Favorites move between devices with a copy/paste code (chosen over automatic sync for simplicity).
- 2026-11-12: Rejected videos are remembered in `rejected.json`, filled automatically when a batch pull request is closed without merging.

## Keeping this file updated

Update this file whenever the app idea, tech stack, commands, or working preferences change.
