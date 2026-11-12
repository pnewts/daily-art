# CLAUDE.md

Read this file before starting any task. Keep it up to date.

## Project overview

A personal app that shows me **one new video a day of a wildly inspiring piece of art**, mostly performance: theatre, dance, clowning, physical theatre and music.

- **Who uses it:** Just me
- **Platform:** a web page (works on phone and computer)

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
- Testing tricks: `?date=YYYY-MM-DD` pretends it's another day; `?video=<id>` shows a specific video.

### Next steps / open questions

- Automatic search to add new videos (needs a YouTube API key and something that runs on a schedule).
- Put the page online. GitHub Pages needs a public repo on the free plan; Netlify or Cloudflare Pages work with private repos.
- Maybe later: a daily notification, syncing favorites across devices.

## How to work with me

- I'm a beginner. Explain what you're doing and why in plain language. Avoid jargon, or define it when you use it.
- Check with me before big changes, like adding a library, restructuring the project, or deleting files.
- When I need to run something, give me the exact command and tell me what I should see if it worked.
- If something goes wrong, tell me plainly what happened and what you suggest next.

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

## Keeping this file updated

Update this file whenever the app idea, tech stack, commands, or working preferences change.
